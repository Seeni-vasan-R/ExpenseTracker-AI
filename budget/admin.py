from django.contrib import admin

from .models import Budget


@admin.action(description="Activate selected budgets")
def activate_budgets(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Deactivate selected budgets")
def deactivate_budgets(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "category",
        "budget_limit",
        "start_date",
        "end_date",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "category",
        "start_date",
        "end_date",
    )

    search_fields = (
        "user__username",
        "user__email",
        "category__name",
    )

    date_hierarchy = "start_date"

    list_select_related = (
        "user",
        "category",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-start_date",
        "-created_at",
    )

    actions = (
        activate_budgets,
        deactivate_budgets,
    )