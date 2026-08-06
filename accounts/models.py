from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


def profile_picture_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'profile_pictures/user_{instance.user.id}.{ext}'


class UserProfile(models.Model):
    class Theme(models.TextChoices):
        LIGHT = 'light', _('Light')
        DARK = 'dark', _('Dark')

    class Currency(models.TextChoices):
        INR = 'INR', _('Indian Rupee (₹)')
        USD = 'USD', _('US Dollar ($)')
        EUR = 'EUR', _('Euro (€)')
        GBP = 'GBP', _('British Pound (£)')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    profile_picture = models.ImageField(
        upload_to=profile_picture_path,
        default='profile_pictures/default.png',
        blank=True,
        null=True
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    country = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.INR
    )
    theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.LIGHT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Profile"