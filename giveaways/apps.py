from django.apps import AppConfig


class GiveawaysConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "giveaways"

    def ready(self) -> None:
        # flake8: noqa
        import giveaways.signals
