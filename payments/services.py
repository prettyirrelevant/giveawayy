import json
import logging
from typing import Union
from uuid import uuid4

import requests
from django.conf import settings
from django.db import transaction
from giveaways.enums import GiveawayStatus
from giveaways.models import Giveaway
from requests.exceptions import RequestException

from .models import Transaction, TransactionStatus

logger = logging.getLogger(__name__)


class Paystack:
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    requests = requests

    def __init__(self) -> None:
        pass

    def generate_txn_ref(self):
        return uuid4().hex

    def create_transaction_payload(self, amount, email, reference):
        return {
            "reference": reference,
            "amount": str(amount * 100),
            "currency": "NGN",
            "channels": ["card", "bank"],
            "callback_url": settings.PAYSTACK_CALLBACK_URL,
            "email": email,
        }

    def initialize_transaction(self, giveaway) -> str or None:
        txn_ref = self.generate_txn_ref()

        payload = self.create_transaction_payload(
            giveaway.monetary_prize.amount,
            giveaway.creator.email,
            txn_ref,
        )
        try:
            response = requests.post(
                f"{settings.PAYSTACK_URL}/transaction/initialize",
                data=json.dumps(payload),
                headers=self.headers,
            )

            return (
                (response.json()["data"]["authorization_url"], txn_ref)
                if response.status_code == 200
                else (None, None)
            )
        except RequestException as err:
            logger.exception(err)
            return (None, None)

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

    @transaction.atomic
    def verify_transaction(self, reference) -> Union[bool, str, Giveaway]:
        response = requests.get(
            f"{settings.PAYSTACK_URL}/transaction/verify/{reference}", headers=self.headers
        )
        payload = response.json()

        status = self.validate_transaction_payload(payload)
        if status:
            try:
                txn = Transaction.objects.select_related("giveaway").get(id=reference)

                # use webhook during live & staging
                if settings.DEBUG:
                    txn.status = TransactionStatus.SUCCESS
                    txn.giveaway.status = GiveawayStatus.ACTIVE
                    txn.gateway_response = payload["data"]["gateway_response"]

                    txn.giveaway.save()
                    return True, "Giveaway topup was successful!", Giveaway
                else:
                    txn.status = TransactionStatus.PENDING
                    txn.save()

                    return (
                        True,
                        "Your topup is pending. Wait a while before trying to top up again.",
                        Giveaway,
                    )
            except Transaction.DoesNotExist:
                logger.warning(f"No transaction found for ID -> {reference}")
                return False, "Transaction not found!"
        else:
            try:
                txn = Transaction.objects.select_related("giveaway").get(id=reference)
                txn.status = TransactionStatus.FAILED
                txn.gateway_response = payload["data"]["gateway_response"]
                txn.save()

                return False, "Your top up failed!"
            except Transaction.DoesNotExist:
                logger.warning(f"No transaction found for ID -> {reference}")
                return False, "Transaction not found!"

    def validate_transaction_payload(self, payload: dict) -> bool:
        if payload["status"]:
            if payload["data"]["status"] == "failed":
                return False
            elif payload["data"]["status"] == "success":
                return True
        return False


paystack = Paystack()
