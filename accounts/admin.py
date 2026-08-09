from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for user profiles.
    """

    list_display = (
        "user",
        "phone_number",
        "country",
        "currency",
        "theme",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "currency",
        "theme",
        "country",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone_number",
        "country",
    )

    autocomplete_fields = (
        "user",
    )

    list_select_related = (
        "user",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25

    fieldsets = (
        (
            "User",
            {
                "fields": (
                    "user",
                ),
            },
        ),
        (
            "Profile Information",
            {
                "fields": (
                    "profile_picture",
                    "phone_number",
                    "country",
                ),
            },
        ),
        (
            "Preferences",
            {
                "fields": (
                    "currency",
                    "theme",
                ),
            },
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )