import json
import uuid

import redis
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import generic
from formtools.wizard import views
from payments.models import Transaction

from .decorators import giveaway_is_active, giveaway_participants_limit, participant_is_not_creator
from .enums import GiveawayStatus
from .forms import (
    CreateGiveawayAddPasswordForm,
    CreateGiveawayBasicInformationForm,
    CreateGiveawayMonetaryPrizeForm,
    CreateGiveawayQuizCategoryForm,
    JoinGiveawayForm,
    JoinGiveawayQuizForm,
    PrivateGiveawayEntryForm,
)
from .models import Giveaway, Participant
from .utils import (
    calculate_quiz_score,
    create_new_giveaway,
    format_questions_and_answers,
    get_quiz_url,
    show_add_password_if_not_public,
    show_quiz_step_if_category,
)

r = redis.StrictRedis.from_url(settings.REDIS_URL)


@method_decorator(login_required, name="dispatch")
class CreateGiveawayView(views.SessionWizardView):
    condition_dict = {
        "quiz": show_quiz_step_if_category,
        "security": show_add_password_if_not_public,
    }

    form_list = [
        ("basic", CreateGiveawayBasicInformationForm),
        ("quiz", CreateGiveawayQuizCategoryForm),
        ("monetary", CreateGiveawayMonetaryPrizeForm),
        ("security", CreateGiveawayAddPasswordForm),
    ]
    template_name = "giveaways/create.html"

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context["title"] = "Create Giveaway | Giveaway"

        return context

    def done(self, form_list, **kwargs):
        form_dict = kwargs.get("form_dict")
        new_giveaway = create_new_giveaway(self.request.user, form_dict)

        return redirect(reverse("giveaways:view-giveaway", kwargs={"slug": new_giveaway.slug}))


class DisplayGiveawayView(generic.DetailView):
    template_name = "giveaways/view.html"
    model = Giveaway
    slug_field = "slug"
    context_object_name = "giveaway"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("monetary_prize", "creator", "quiz_category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _object = context["giveaway"]
        context["title"] = f"{_object.title} | Giveaway"

        if (
            _object.creator.username == self.request.user.username
            and _object.status == GiveawayStatus.CREATED
        ):
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            }
            txn_ref = uuid.uuid4().hex
            payload = {
                "reference": txn_ref,
                "amount": str(_object.monetary_prize.amount * 100),
                "currency": "NGN",
                "channels": ["card", "bank"],
                "callback_url": settings.PAYSTACK_CALLBACK_URL,
                "email": _object.creator.email,
            }

            response = requests.post(
                f"{settings.PAYSTACK_URL}/transaction/initialize",
                data=json.dumps(payload),
                headers=headers,
            )

            new_transaction = Transaction.objects.create(
                id=txn_ref,
                giveaway=_object,
                narration=f"top_up_{txn_ref}",
                amount=_object.monetary_prize.amount,
            )
            context["topup_url"] = response.json()["data"]["authorization_url"]

        return context


@method_decorator(
    [participant_is_not_creator, giveaway_is_active, giveaway_participants_limit], name="dispatch"
)
class JoinGiveawayView(generic.TemplateView):
    template_name = "giveaways/join.html"

    join_giveaway_form = JoinGiveawayForm
    private_giveaway_entry_form = PrivateGiveawayEntryForm
    quiz_form = JoinGiveawayQuizForm

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # This is basically a check against `get_context_data` method whereby
        # the API request to get questions does not return a status code of 200.
        if context["giveaway"].is_category_quiz and not context.get("quiz_form"):
            messages.error(
                request, "Unable to get quiz at the moment. Please try again after a while."
            )
            return redirect(
                reverse("giveaways:view-giveaway", kwargs={"slug": context["giveaway"].slug})
            )
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["giveaway"] = get_object_or_404(
            Giveaway.objects.select_related("creator", "quiz_category"),
            slug=self.kwargs.get("slug"),
        )
        giveaway = context["giveaway"]

        context["title"] = f"Join {giveaway.title}| Giveaway"
        context["join_giveaway_form"] = self.join_giveaway_form(prefix="join_giveaway_pre")
        context["private_giveaway_entry_form"] = self.private_giveaway_entry_form(
            prefix="private_entry_pre", giveaway=giveaway
        )

        if giveaway.is_category_quiz:
            quiz_url = get_quiz_url(giveaway.quiz_category.choice)
            response = requests.get(quiz_url)

            if response.status_code == 200:
                questions, answers = format_questions_and_answers(response.json()["results"])

                # store answers in redis
                r.set(f'quiz:{answers["quiz_id"]}', json.dumps(answers))

                # Store the questions in session.
                # They are deleted on every valid or tampered `POST` request.
                self.request.session["questions"] = questions

                context["quiz_form"] = self.quiz_form(questions=questions, prefix="quiz_pre")

        return context

    def post(self, *args, **kwargs):
        quiz_form = None
        context = {}
        giveaway = self.get_context_data()["giveaway"]

        if giveaway.is_category_quiz:
            quiz_form = self.get_form(self.request, self.quiz_form, prefix="quiz_pre")

        private_giveaway_entry_form = self.get_form(
            self.request, self.private_giveaway_entry_form, "private_entry_pre"
        )
        join_giveaway_form = self.get_form(
            self.request, self.join_giveaway_form, "join_giveaway_pre"
        )

        if private_giveaway_entry_form.is_valid():
            self.request.session[giveaway.slug] = True
            return redirect(reverse("giveaways:join-giveaway", kwargs={"slug": giveaway.slug}))

        elif join_giveaway_form.is_valid():
            # If the giveaway contains quiz. The participant is created with a flag `is_eligible=False`,
            # the flag will updated when the quiz has been answered.
            # Otherwise the flag `is_eligible=True` if no quiz is present.
            if giveaway.is_category_quiz:

                # checks if participant already registered with that account number for the giveaway
                participant_exists = giveaway.participants.filter(
                    account_number=join_giveaway_form.cleaned_data.get("account_number")
                ).exists()
                if not participant_exists:
                    new_participant = Participant.objects.create(
                        **join_giveaway_form.cleaned_data, giveaway=giveaway
                    )
                    self.request.session["account_number"] = new_participant.account_number
                    return redirect(
                        reverse("giveaways:join-giveaway", kwargs={"slug": giveaway.slug})
                    )

                join_giveaway_form.add_error(
                    None, "You cannot use the same account number multiple times."
                )
            else:
                participant_exists = giveaway.participants.filter(
                    account_number=join_giveaway_form.cleaned_data.get("account_number")
                ).exists()

                if not participant_exists:
                    new_participant = Participant.objects.create(
                        **join_giveaway_form.cleaned_data, giveaway=giveaway, is_eligible=True
                    )
                    messages.success(
                        self.request,
                        "You have successfully joined this giveaway. You will contacted via email if selected. Goodluck!",
                    )

                    #######################################
                    self.request.session.pop(giveaway.slug, None)
                    self.request.session.pop("account_number", None)
                    #######################################

                    return redirect(
                        reverse("giveaways:view-giveaway", kwargs={"slug": giveaway.slug})
                    )

                join_giveaway_form.add_error(
                    None, "You cannot use the same account number multiple times."
                )

        # First checks if there is a quiz form based on the giveaway.
        # Then checks if the form is valid.
        elif quiz_form and quiz_form.is_valid():

            # using POST data directly instead of `cleaned_data` property of the form.
            # there's a bug somewhere though.
            cleaned_data = self.request.POST.copy().dict()
            quiz_id = cleaned_data.pop("quiz_pre-quiz_id")

            redis_quiz_answers = r.get(f"quiz:{quiz_id}")

            # if the quiz answers are not present in redis
            # or the field was tampered with by the user.
            if not redis_quiz_answers:
                messages.error(
                    self.request, "Sorry, something went wrong validating quiz answers."
                )
                # delete the questions from session.
                del self.request.session["questions"]

                return redirect(reverse("giveaways:join-giveaway", kwargs={"slug": giveaway.slug}))

            cleaned_data.pop("quiz_pre-timer")
            cleaned_data.pop("csrfmiddlewaretoken")

            answers = json.loads(redis_quiz_answers)
            score = calculate_quiz_score(cleaned_data, answers["answers"])

            if score >= 50:
                participant = get_object_or_404(
                    giveaway.participants.get_queryset(),
                    account_number=self.request.session["account_number"],
                )
                participant.is_eligible = True
                participant.save()

                messages.success(
                    self.request,
                    "You have successfully joined this giveaway. You will contacted via email if selected. Goodluck!",
                )
            ########################################
            self.request.session.pop(giveaway.slug, None)  #
            self.request.session.pop("account_number", None)  #
            self.request.session.pop("questions", None)  #
            #######################################

            messages.error(
                self.request,
                "Sorry, you did not get up to the required percentage. Try again",
            )
            return redirect(reverse("giveaways:view-giveaway", kwargs={"slug": giveaway.slug}))

        context["quiz_form"] = quiz_form

        context["giveaway"] = giveaway
        context["private_giveaway_entry_form"] = private_giveaway_entry_form
        context["join_giveaway_form"] = join_giveaway_form
        context["title"] = f"Join {giveaway.title}| Giveaway"

        return render(self.request, self.template_name, context)

    def get_form(self, request, formcls, prefix):
        """Gets the form's POST data based on `request` and `prefix`"""
        keys = [key.split("-")[0] for key in request.POST.keys()]
        data = request.POST if prefix in keys else None

        # Each form with different params determined using `prefix`
        if prefix == "private_entry_pre":
            return formcls(data, prefix=prefix, giveaway=self.get_context_data()["giveaway"])
        elif prefix == "join_giveaway_pre":
            return formcls(data, prefix=prefix)
        elif prefix == "quiz_pre":
            return formcls(data, prefix=prefix, questions=self.request.session["questions"])


class SearchGiveawayView(generic.ListView):
    template_name = "giveaways/search.html"
    context_object_name = "giveaways"
    model = Giveaway
    paginate_by = 4

    def get_queryset(self):
        query = self.request.GET.get("q")
        queryset = (
            self.model.objects.search(query)
            .select_related("monetary_prize", "creator", "quiz_category")
            .prefetch_related("participants")
            .filter(is_public=True)
            .order_by("-created_at")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q")

        return context
