from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


def profile_picture_path(instance: "UserProfile", filename: str) -> str:
    """
    Generate a unique upload path for a user's profile picture.

    A UUID prevents files with the same filename from overwriting
    another uploaded file.
    """
    extension = Path(filename).suffix.lower()

    if not extension:
        extension = ".jpg"

    return f"profile_pictures/user_{instance.user_id}/{uuid4().hex}{extension}"


class UserProfile(models.Model):
    """
    Stores optional user preferences and profile information.

    Authentication fields such as username, email, and password belong
    to Django's configured User model.
    """

    class Theme(models.TextChoices):
        LIGHT = "light", _("Light")
        DARK = "dark", _("Dark")

    class Currency(models.TextChoices):
        INR = "INR", _("Indian Rupee (₹)")
        USD = "USD", _("US Dollar ($)")
        EUR = "EUR", _("Euro (€)")
        GBP = "GBP", _("British Pound (£)")

    phone_validator = RegexValidator(
        regex=r"^\+?[1-9]\d{7,14}$",
        message=_(
            "Enter a valid international phone number, for example "
            "+919876543210."
        ),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    profile_picture = models.ImageField(
        upload_to=profile_picture_path,
        default="profile_pictures/default.png",
        blank=True,
    )

    phone_number = models.CharField(
        max_length=16,
        validators=[phone_validator],
        blank=True,
    )

    country = models.CharField(
        max_length=100,
        blank=True,
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.INR,
    )

    theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.LIGHT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = _("User profile")
        verbose_name_plural = _("User profiles")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        username = getattr(self.user, "username", self.user_id)
        return f"{username}'s Profile"