from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "category",
        "budget_limit",
        "start_date",
        "end_date",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "user__username",
        "category__name",
    )