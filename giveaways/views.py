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

        if _object.creator.username == self.request.user.username:
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
                "callback_url": "http://localhost:8000/payments/callback/",
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
            # checks if there are questions present in session due to an invalid `POST` request.
            if self.request.session.get("questions") and self.request.method == "POST":
                context["quiz_form"] = self.quiz_form(
                    questions=self.request.session.get("questions"), prefix="quiz_pre"
                )

            else:
                quiz_url = get_quiz_url(giveaway.quiz_category.choice)
                response = requests.get(quiz_url)

                if response.status_code == 200:
                    questions, answers = format_questions_and_answers(response.json()["results"])

                    # store answers in redis
                    r.set(f'quiz:{answers["quiz_id"]}', json.dumps(answers))

                    # Store the questions in session.
                    # They are deleted on every **valid** or tampered `POST` request.
                    self.request.session["questions"] = questions

                    context["quiz_form"] = self.quiz_form(questions=questions, prefix="quiz_pre")

        return context

    def post(self, *args, **kwargs):
        quiz_form = None

        context = {}
        giveaway = self.get_context_data()["giveaway"]

        if giveaway.is_category_quiz:
            quiz_form = self.get_form(self.request, self.quiz_form, "quiz_pre")

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
            if giveaway.is_category_quiz:
                # checks if participant already registered with that account number
                participant_exists = Participant.objects.filter(
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
                participant_exists = Participant.objects.filter(
                    account_number=join_giveaway_form.cleaned_data.get("account_number")
                ).exists()
                if not participant_exists:
                    new_participant = Participant.objects.create(
                        **join_giveaway_form.cleaned_data, giveaway=giveaway, is_eligible=True
                    )
                    self.request.session["account_number"] = new_participant.account_number
                    messages.success(
                        self.request,
                        "You have successfully joined this giveaway. You will contacted via email if selected. Goodluck!",
                    )
                    return redirect(
                        reverse("giveaways:join-giveaway", kwargs={"slug": giveaway.slug})
                    )

                join_giveaway_form.add_error(
                    None, "You cannot use the same account number multiple times."
                )

        # First checks if there is a quiz form based on the giveaway.
        # Then checks if the form is valid.
        elif quiz_form:
            if quiz_form.is_valid():
                cleaned_data = quiz_form.cleaned_data
                redis_quiz_answers = r.get(f'quiz:{cleaned_data.get("quiz_id")}')

                # if the quiz answers are not present in redis
                # or the field was tampered with by the user.
                if not redis_quiz_answers:
                    messages.error(
                        self.request, "Sorry, something went wrong validating quiz answers."
                    )
                    # delete the questions from session.
                    del self.request.session["questions"]

                    return redirect(
                        reverse("giveaways:join-giveaway", kwargs={"slug": giveaway.slug})
                    )
                answers = json.loads(redis_quiz_answers)
                score = calculate_quiz_score(cleaned_data, answers["answers"])

                if score >= 50:
                    participant = get_object_or_404(
                        Participant, account_number=self.request.session["account_number"]
                    )
                    participant.is_eligible = True
                    participant.save()

                    messages.success(
                        self.request,
                        "You have successfully joined this giveaway. You will contacted via email if selected. Goodluck!",
                    )
                try:
                    del self.request.session["account_number"]
                    del self.request.session["questions"]
                    del self.request.session[giveaway.slug]
                except KeyError:
                    pass

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
        data = (
            request.POST if prefix in [key.split("-")[0] for key in request.POST.keys()] else None
        )
        # Each form with different params determined using `prefix`
        if prefix == "private_entry_pre":
            return formcls(data, prefix=prefix, giveaway=self.get_context_data()["giveaway"])
        elif prefix == "quiz_pre":
            return formcls(data, prefix=prefix, questions=self.request.session["questions"])
        elif prefix == "join_giveaway_pre":
            return formcls(data, prefix=prefix)
