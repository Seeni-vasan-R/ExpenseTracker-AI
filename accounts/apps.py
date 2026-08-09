from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration for the accounts application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Accounts"

    def ready(self) -> None:
        """
        Import signal handlers when Django starts.
        """
        from . import signals  # noqa: F401