from django.contrib import admin

from .models import AISummary


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "year",
        "month",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "year",
        "month",
    )

    search_fields = (
        "user__username",
        "summary_text",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-year",
        "-month",
        "-created_at",
    )