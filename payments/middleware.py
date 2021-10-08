import hashlib
import hmac

from django.conf import settings
from django.http import HttpRequest
from django.http.response import HttpResponseNotFound


class PaystackMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        return response

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        if view_func.__name__ == "WebhookView":
            hash = hmac.new(
                settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
                request.body,
                digestmod=hashlib.sha512,
            ).hexdigest()

            hash_from_request = request.META.get("HTTP_X_PAYSTACK_SIGNATURE")
            if hash_from_request:
                return (
                    None
                    if hmac.compare_digest(hash, hash_from_request)
                    else HttpResponseNotFound()
                )

            return HttpResponseNotFound()

        return None
