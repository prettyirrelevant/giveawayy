from logging import getLogger

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import User
from .tokens import account_activation_token, account_password_reset_token

logger = getLogger(__name__)


def send_activation_email(user_pk: int):
    """Utility function to send activation emails."""
    logger.info(f"Sending activation email to: {user_pk}")
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(f"EMAIL ERROR: User does not exist -> {user_pk}")
        pass

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    subject = "[Giveaway] Please Activate Your Account"
    html_content = render_to_string(
        "accounts/emails/account_activation.html",
        {"first_name": user.first_name, "last_name": user.last_name, "token": token, "uid": uid},
    )

    mail = EmailMultiAlternatives(subject, to=[user.email])
    mail.attach_alternative(html_content, "text/html")

    mail.send()
    logger.info(f"Activation email successfully sent to -> {user.username}")


def send_password_reset_email(email: str):
    """Utility function to send password reset emails."""
    logger.info(f"Sending password reset email to: {email}")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        logger.warning(f"EMAIL ERROR: User does not exist -> {email}")
        user = None

    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_password_reset_token.make_token(user)
        subject = "[Giveaway] Resest Your Password"
        html_content = render_to_string(
            "accounts/emails/reset_password_mail.html",
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "token": token,
                "uid": uid,
            },
        )

        mail = EmailMultiAlternatives(subject, to=[user.email])
        mail.attach_alternative(html_content, "text/html")

        mail.send()
        logger.info(f"Password reset email successfully sent to -> {user.username}")


def verify_uid_and_token(uid: str, token: str, type: str):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if type == "activation":
        if user is not None and account_activation_token.check_token(user, token):
            return (user, True)
    elif type == "reset":
        if user is not None and account_password_reset_token.check_token(user, token):
            return (user, True)

    return (user, False)
