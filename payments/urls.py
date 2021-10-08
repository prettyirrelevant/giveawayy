from django.urls import path

from . import views

app_name = "payments"
urlpatterns = [
    path("payments/callback/", views.TopupCallbackView.as_view(), name="callback"),
    path("payments/webhook/", views.WebhookView.as_view(), name="webhook"),
]
