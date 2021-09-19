from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    username = models.CharField(
        _("username"),
        max_length=20,
        unique=True,
        null=False,
        blank=False,
        db_index=True,
        validators=[UnicodeUsernameValidator()],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        blank=False,
        null=False,
        db_index=True,
        error_messages={
            "unique": _("A user with that email address already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=100, blank=False, null=False)
    last_name = models.CharField(_("last name"), max_length=100, blank=False, null=False)
    is_email_verified = models.BooleanField(
        _("is email verified"),
        help_text=_("Designates whether the user has verified the email address"),
        default=False,
    )
    email_verified_at = models.DateTimeField(_("email verified at"), blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    # @property
    # def profile_url(self):
    #     hex_name = self.get_full_name().encode().hex()
    #     return f"https://avatars.dicebear.com/api/bottts/{hex_name}.svg?size=16"
