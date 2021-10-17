import logging
from uuid import uuid4

import requests
from django.conf import settings
from django.db import transaction
from giveaways.enums import GiveawayStatus
from giveaways.models import Giveaway
from requests.exceptions import RequestException

from .models import Transaction, TransactionStatus

logger = logging.getLogger(__name__)

# TODO: Payout to giveaway winners
# TODO: Improve error handling
# TODO: Mark pending transactions over 24 hours as `FAILED`
# TODO: Delete giveaways.
# TODO: Incorporate Buycoins.


class Paystack:
    headers = {
        "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    def __init__(self):
        self.requests = requests.Session()

    def generate_txn_ref(self):
        return uuid4().hex

    @transaction.atomic()
    def create_new_transaction(self, giveaway):
        authorization_url, reference = self.initialize_transaction(giveaway)

        if authorization_url:
            new_transaction = Transaction.objects.create(
                id=reference,
                giveaway=giveaway,
                narration=f"top_up_{reference}",
                amount=giveaway.monetary_prize.amount,
            )

        return authorization_url

    def verify_transaction(self, reference):
        response = self.requests.get(f"{settings.PAYSTACK_URL}/transaction/verify/{reference}")
        payload = response.json()

        status, message, giveaway = self.validate_transaction_payload(payload, reference)
        return status, message, giveaway

    def initiate_bulk_transfer(self, payload):
        try:
            response = self.requests.post(f"{settings.PAYSTACK_URL}/transfer/bulk", json=payload)
            if response.status_code == 200:
                return response.json()
        except RequestException as err:
            logger.exception(err)
            raise err

    def create_transfer_recipient(self, payload):
        try:
            response = self.requests.post(
                f"{settings.PAYSTACK_URL}/transferrecipient", json=payload
            )
            if response.status_code == 200:
                response = response.json()
                return response["recipient_code"]
        except RequestException as err:
            logger.exception(err)
            return None

    def create_transaction_payload(self, amount, email, reference):
        return {
            "reference": reference,
            "amount": str(amount * 100),
            "currency": "NGN",
            "channels": ["card", "bank"],
            "callback_url": settings.PAYSTACK_CALLBACK_URL,
            "email": email,
        }

    def initialize_transaction(self, giveaway):
        txn_ref = self.generate_txn_ref()

        payload = self.create_transaction_payload(
            giveaway.monetary_prize.amount,
            giveaway.creator.email,
            txn_ref,
        )
        try:
            response = self.requests.post(
                f"{settings.PAYSTACK_URL}/transaction/initialize", json=payload
            )

            return (
                (response.json()["data"]["authorization_url"], txn_ref)
                if response.status_code == 200
                else (None, None)
            )
        except RequestException as err:
            logger.exception(err)
            return (None, None)

    @transaction.atomic
    def validate_transaction_payload(self, payload: dict, reference: str):
        if payload["status"]:
            if payload["data"]["status"] == "failed":
                try:
                    txn = Transaction.objects.select_related("giveaway").get(id=reference)
                    txn.status = TransactionStatus.FAILED
                    txn.gateway_response = payload["data"]["gateway_response"]
                    txn.save()

                    return (False, "Your top up failed!", None)
                except Transaction.DoesNotExist:
                    logger.warning(f"No transaction found for ID -> {reference}")
                    return (False, "Transaction not found!", None)

            elif payload["data"]["status"] == "success":
                try:
                    txn = Transaction.objects.select_related("giveaway").get(id=reference)
                    # use webhook during live & staging
                    if settings.DEBUG:
                        txn.status = TransactionStatus.SUCCESS
                        txn.giveaway.status = GiveawayStatus.ACTIVE
                        txn.gateway_response = payload["data"]["gateway_response"]

                        txn.giveaway.save()
                        txn.save()
                        return (True, "Giveaway topup was successful!", txn.giveaway)
                    else:
                        txn.status = TransactionStatus.PENDING
                        txn.save()

                        return (
                            True,
                            "Your topup is pending. Wait a while before trying to top up again.",
                            txn.giveaway,
                        )
                except Transaction.DoesNotExist:
                    logger.warning(f"No transaction found for ID -> {reference}")
                    return (False, "Transaction not found!", None)
        return (False, "", None)

    def create_bulk_transfers_payload(self, recipients, amount, giveaway):
        transfers = []

        for recipient in recipients:
            new_txn = Transaction.objects.create(
                id=self.generate_txn_ref(),
                giveaway=giveaway,
                narration=f"credit_{recipient}",
                amount=amount,
                status=TransactionStatus.INITIATED,
            )
            amount_in_kobo = format(amount * 100, ".3f")
            transfers.append(
                {
                    "reference": new_txn.id,
                    "recipient": recipient,
                    "amount": amount_in_kobo,
                }
            )
        return {"source": "balance", "currency": "NGN", "transfers": transfers}


paystack = Paystack()
