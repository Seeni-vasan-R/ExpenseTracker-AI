from django.contrib import admin

from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category_type",
        "user",
        "is_default",
        "created_at",
    )

    list_filter = (
        "category_type",
        "is_default",
    )

    search_fields = (
        "name",
        "user__username",
    )

    ordering = (
        "name",
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
        "transaction_time",
        "is_deleted",
    )

    list_filter = (
        "transaction_type",
        "payment_method",
        "transaction_date",
        "is_deleted",
    )

    search_fields = (
        "user__username",
        "description",
        "category__name",
    )

    ordering = (
        "-transaction_date",
        "-transaction_time",
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )

    list_select_related = (
        "user",
        "category",
    )