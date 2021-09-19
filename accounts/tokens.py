from django.contrib.auth.tokens import PasswordResetTokenGenerator


class UserActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp: int) -> str:
        return f"{user.pk}{user.is_email_verified}{timestamp}"


account_activation_token = UserActivationTokenGenerator()
account_password_reset_token = PasswordResetTokenGenerator()
