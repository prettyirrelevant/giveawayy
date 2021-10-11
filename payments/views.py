import json

from django.contrib import messages
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from .services import paystack
from .tasks import handle_webhook


class PaystackTopupCallbackView(generic.View):
    def get(self, request, *args, **kwargs):
        txn_ref = request.GET.get("reference")

        if txn_ref:
            status, message, giveaway = paystack.verify_transaction(txn_ref)
            if status:
                messages.success(request, message)
                return redirect(reverse("giveaways:view-giveaway", kwargs={"slug": giveaway.slug}))
            else:
                messages.error(request, message)
                return redirect(reverse("giveaways:view-giveaway", kwargs={"slug": giveaway.slug}))

        # Something sus.
        print("Invalid reference....", txn_ref)
        return redirect(reverse("core:index"))


class PaystackWebhookView(generic.View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))

        print(data)

        handle_webhook(data)

        return JsonResponse(data={})
