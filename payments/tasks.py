from logging import getLogger

from giveaways.enums import GiveawayStatus
from giveaways.models import Giveaway, Participant
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from .enums import TransactionStatus
from .models import Transaction
from .services import paystack

logger = getLogger("huey")


@db_task()
def handle_webhook(payload: dict):
    logger.info(f"Handling webhook of event -> {payload['event']}")

    if payload["event"] == "charge.success":
        transaction_ref = payload["data"]["reference"]
        try:
            transaction = Transaction.objects.select_related("giveaway").get(id=transaction_ref)
            transaction.status = TransactionStatus.SUCCESS
            transaction.giveaway.status = GiveawayStatus.ACTIVE

            transaction.giveaway.save()
            transaction.save()
        except Transaction.DoesNotExist:
            logger.error(f"Unable to find transaction with ID -> {transaction_ref}")


@db_task()
def populate_recipient_code(participant_id):
    participant = Participant.objects.get(pk=participant_id)
    payload = {
        "type": "nuban",
        "name": participant.name,
        "account_number": participant.account_number,
        "bank_code": participant.bank_code,
    }
    recipient_code = paystack.create_transfer_recipient(payload)
    if recipient_code:
        participant.recipient_code = recipient_code
        participant.save()


@db_periodic_task(crontab(hour="*/1"))
def credit_giveaway_winners():
    logger.info("Trying to credit giveaway winners...")

    ended_giveaways = (
        Giveaway.objects.prefetch_related("participants")
        .filter(
            has_winners=True,
            paid_winners=False,
            status=GiveawayStatus.ENDED,
        )
        .all()
    )

    for giveaway in ended_giveaways:
        winners = list(
            giveaway.participants.filter(is_winner=True, is_paid=False)
            .all()
            .values("recipient_code", "email")
        )
        winners_count = giveaway.participants.filter(is_winner=True).count()
        amount_to_be_paid = giveaway.monetary_prize.net_amount / winners_count
        # rddhdniksn
        payload = paystack.create_bulk_transfers_payload(winners, amount_to_be_paid, giveaway)
        transfer_response = paystack.initiate_bulk_transfer(payload)
        for transfer in transfer_response["data"]:
            txn = Transaction.objects.filter()
