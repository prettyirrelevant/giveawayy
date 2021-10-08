import functools

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from giveaways.enums import GiveawayStatus

from .models import Giveaway


def participant_is_not_creator(f):
    @functools.wraps(f)
    def decorator(request, *args, **kwargs):
        slug = kwargs.get("slug")
        giveaway = get_object_or_404(Giveaway.objects.select_related("creator"), slug=slug)

        if giveaway.creator != request.user:
            return f(request, *args, **kwargs)

        messages.error(request, "You cannot join a giveaway you created!")
        return redirect(reverse("giveaways:view-giveaway", kwargs={"slug": slug}))

    return decorator


def giveaway_is_active(f):
    @functools.wraps(f)
    def decorator(request, *args, **kwargs):
        slug = kwargs.get("slug")
        giveaway = get_object_or_404(Giveaway, slug=slug)

        if giveaway.status == GiveawayStatus.ACTIVE:
            return f(request, *args, **kwargs)

        messages.error(request, "You can only join giveaways that are active")
        return redirect(reverse("giveaways:view-giveaway", kwargs={"slug": slug}))

    return decorator


def giveaway_participants_limit(f):
    @functools.wraps(f)
    def decorator(request, *args, **kwargs):
        slug = kwargs.get("slug")
        giveaway = get_object_or_404(Giveaway.objects.prefetch_related("participants"), slug=slug)

        if giveaway.participants.count() < giveaway.number_of_participants:
            return f(request, *args, **kwargs)

        messages.error(
            request,
            "The maximum number of participants for this giveaway has been reached. Better luck next time!",
        )
        return redirect(reverse("giveaways:view-giveaway", kwargs={"slug": slug}))

    return decorator
