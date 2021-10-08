from django.urls import path

from . import views

app_name = "giveaways"
urlpatterns = [
    path("giveaways/new/", views.CreateGiveawayView.as_view(), name="create-giveaway"),
    path("giveaways/<slug>/", views.DisplayGiveawayView.as_view(), name="view-giveaway"),
    path("giveaways/<slug>/join/", views.JoinGiveawayView.as_view(), name="join-giveaway"),
]
