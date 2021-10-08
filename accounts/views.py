from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import LoginView as _LoginView
from django.contrib.auth.views import LogoutView as _LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.generic.base import TemplateView

from .forms import PasswordResetRequestForm, UserLoginForm, UserRegistrationForm
from .utils import send_activation_email, send_password_reset_email, verify_uid_and_token


class RegistrationView(SuccessMessageMixin, generic.CreateView):
    form_class = UserRegistrationForm
    template_name = "accounts/registration.html"
    success_message = "Your account was created successfully. Check email for activation!"
    success_url = reverse_lazy("accounts:login")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Registration"

        return context

    def form_valid(self, form) -> HttpResponse:
        _ = super().form_valid(form)

        send_activation_email(self.object.pk)
        return redirect(self.get_success_url())


class LoginView(SuccessMessageMixin, _LoginView):
    form_class = UserLoginForm
    template_name = "accounts/login.html"
    success_message = "You have been logged in successfully!"
    extra_context = {"title": "Login | Giveaway"}


class ActivateAccountView(generic.View):
    redirect_url = reverse_lazy("core:index")

    def get(self, request, *args, **kwargs):
        user, is_valid = verify_uid_and_token(kwargs.get("uid"), kwargs.get("token"), "activation")

        if is_valid:
            user.is_email_verified = True
            user.email_verified_at = timezone.now()
            user.save()

            messages.success(request, "Your account has been activated successfully!")
            return redirect(self.redirect_url)

        messages.error(request, "The token has expired, already used or invalid!")
        return redirect(self.redirect_url)


class ForgotPasswordView(SuccessMessageMixin, generic.FormView):
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy("core:index")
    success_message = "Check your email for the instructions to reset your password!"
    template_name = "accounts/forgot_password.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Forgot Password"

        return context

    def form_valid(self, form) -> HttpResponse:
        send_password_reset_email(form.cleaned_data.get("email"))

        return super().form_valid(form)


class ResetPasswordView(SuccessMessageMixin, generic.FormView):
    user = None
    form_class = SetPasswordForm
    success_message = "Your password has been updated successfully!"
    success_url = reverse_lazy("core:index")
    template_name = "accounts/reset_password.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Reset Password"

        return context

    def form_valid(self, form) -> HttpResponse:
        _ = form.save()
        logout(self.request)

        return super().form_valid(form)

    def dispatch(self, request, *args: Any, **kwargs: Any):
        uid, token = kwargs.get("uid"), kwargs.get("token")
        user, is_valid = verify_uid_and_token(uid, token, "reset")

        if is_valid:
            self.user = user
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(request, "The token has expired, already used or invalid!")
            return redirect(reverse("core:index"))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.user

        return kwargs


class LogoutView(_LogoutView):
    def dispatch(self, request, *args, **kwargs):
        logout(request)
        next_page = self.get_next_page()

        messages.success(request, "You have been logged out succesfully!")

        if next_page:
            return HttpResponseRedirect(next_page)

        return super(TemplateView, self).dispatch(request, *args, **kwargs)
