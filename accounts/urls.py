from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("registration/", views.RegistrationView.as_view(), name="registration"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("activate/<uid>/<token>/", views.ActivateAccountView.as_view(), name="activate-account"),
    path("forgot_password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset_password/<uid>/<token>", views.ResetPasswordView.as_view(), name="reset-password"),
]
