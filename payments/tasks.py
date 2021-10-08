from logging import getLogger

from giveaways.enums import GiveawayStatus
from huey.contrib.djhuey import db_task

from payments.enums import TransactionStatus
from payments.models import Transaction

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
