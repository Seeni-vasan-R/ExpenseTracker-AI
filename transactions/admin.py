from django.contrib import admin
from django.utils import timezone

from .models import (
    Category,
    RecurringTransaction,
    Transaction,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category_type",
        "user",
        "is_default",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "category_type",
        "is_default",
        "created_at",
    )

    search_fields = (
        "name",
        "user__username",
        "user__email",
    )

    ordering = (
        "category_type",
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.action(description="Soft-delete selected transactions")
def soft_delete_transactions(modeladmin, request, queryset):
    queryset.filter(is_deleted=False).update(
        is_deleted=True,
        deleted_at=timezone.now(),
    )


@admin.action(description="Restore selected transactions")
def restore_transactions(modeladmin, request, queryset):
    queryset.filter(is_deleted=True).update(
        is_deleted=False,
        deleted_at=None,
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "transaction_type",
        "amount",
        "category",
        "payment_method",
        "transaction_date",
        "is_deleted",
        "is_recurring_generated",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "payment_method",
        "category",
        "is_deleted",
        "is_recurring_generated",
        "transaction_date",
    )

    search_fields = (
        "user__username",
        "user__email",
        "category__name",
        "description",
    )

    date_hierarchy = "transaction_date"

    ordering = (
        "-transaction_date",
        "-created_at",
    )

    list_select_related = (
        "user",
        "category",
        "recurring_source",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )

    actions = (
        soft_delete_transactions,
        restore_transactions,
    )


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "transaction_type",
        "amount",
        "category",
        "frequency",
        "start_date",
        "end_date",
        "next_occurrence",
        "is_active",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "frequency",
        "is_active",
        "category",
        "start_date",
        "next_occurrence",
    )

    search_fields = (
        "user__username",
        "user__email",
        "category__name",
        "description",
    )

    ordering = (
        "next_occurrence",
        "-created_at",
    )

    list_select_related = (
        "user",
        "category",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )