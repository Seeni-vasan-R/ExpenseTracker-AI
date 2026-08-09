from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


User = get_user_model()


@receiver(
    post_save,
    sender=User,
    dispatch_uid="accounts.create_user_profile",
)
def create_user_profile(
    sender,
    instance,
    created: bool,
    **kwargs,
) -> None:
    """
    Create a UserProfile automatically when a new user is created.

    get_or_create() prevents duplicate profiles if the profile was already
    created manually or by another part of the application.
    """
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
        )