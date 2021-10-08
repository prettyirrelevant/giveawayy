from django.urls import path

from . import views

app_name = "payments"
urlpatterns = [
    path(
        "payments/paystack/callback/",
        views.PaystackTopupCallbackView.as_view(),
        name="paystack-callback",
    ),
    path(
        "payments/paystack/webhook/", views.PaystackWebhookView.as_view(), name="paystack-webhook"
    ),
]
