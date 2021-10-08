import json

import requests
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from giveaways.enums import GiveawayStatus

from .enums import TransactionStatus
from .models import Transaction
from .tasks import handle_webhook


class TopupCallbackView(generic.View):
    def get(self, request, *args, **kwargs):
        txn_ref = request.GET.get("reference")
        if txn_ref:
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            }

            response = requests.get(
                f"{settings.PAYSTACK_URL}/transaction/verify/{txn_ref}", headers=headers
            )
            response_data = response.json()

            with transaction.atomic():
                # when status is `True`
                if response_data["status"]:
                    if response_data["data"]["status"] == "failed":
                        try:
                            txn = Transaction.objects.select_related("giveaway").get(id=txn_ref)
                            txn.status = TransactionStatus.FAILED
                            txn.gateway_response = response_data["data"]["gatewa_response"]

                            txn.save()
                        except Transaction.DoesNotExist:
                            pass

                        messages.error(request, "Your top up failed!")
                        return redirect(
                            reverse("giveaways:view-giveaway", kwargs={"slug": txn.giveaway.slug})
                        )
                    elif response_data["data"]["status"] == "success":
                        try:
                            txn = Transaction.objects.select_related("giveaway").get(id=txn_ref)

                            # use webhook during live & staging
                            if settings.DEBUG:
                                txn.status = TransactionStatus.SUCCESS
                                txn.giveaway.status = GiveawayStatus.ACTIVE
                                txn.giveaway.save()
                            else:
                                txn.status = TransactionStatus.PENDING
                            txn.save()
                        except Transaction.DoesNotExist:
                            pass

                        messages.info(request, "Your top up is pending!")
                        return redirect(
                            reverse("giveaways:view-giveaway", kwargs={"slug": txn.giveaway.slug})
                        )

                # when status is `False`
                print("Invalid reference....", txn_ref)
                return redirect(reverse("core:index"))

        # when no `txn_ref `is provided. Something sus!
        return redirect(reverse("core:index"))


class WebhookView(generic.View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))

        print(data)

        handle_webhook(data)

        return JsonResponse(data={})
