import random

from django.db.models import Q
from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from payments.enums import TransactionStatus

from .models import Giveaway, GiveawayStatus


@db_periodic_task(crontab(minute="*/3"))
def change_giveaway_status_on_expiry():
    now = timezone.now()

    all_giveaways = Giveaway.objects.exclude(
        Q(status=GiveawayStatus.ENDED) | Q(end_at__gt=now)
    ).update(status=GiveawayStatus.ENDED)


@db_periodic_task(crontab(minute="*/5"))
def select_giveaway_winners():
    ended_giveaways = (
        Giveaway.objects.prefetch_related("participants")
        .filter(
            has_winners=False,
            status=GiveawayStatus.ENDED,
            transactions__narration__startswith="top_up_",
            transactions__status=TransactionStatus.SUCCESS,
        )
        .all()
    )

    for giveaway in ended_giveaways:
        no_of_winners = giveaway.number_of_winners
        eligible_participants = giveaway.participants.filter(is_eligible=True)

        if eligible_participants.count() > 0:
            # update no_of_winners when eligible participants are less than the required.
            no_of_winners = (
                eligible_participants.count()
                if eligible_participants.count() < no_of_winners
                else no_of_winners
            )

            winners = random.sample(
                list(eligible_participants.values_list("account_number", flat=True)),
                k=no_of_winners,
            )
            winners = eligible_participants.filter(account_number__in=winners).update(
                is_winner=True
            )
            giveaway.has_winners = True
            giveaway.save()
