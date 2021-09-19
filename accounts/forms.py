from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password1", "password2")


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address", widget=forms.EmailInput(attrs={"autofocus": True})
    )


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email Address", max_length=254)
