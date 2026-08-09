from django.urls import path

from .views import (
    CategoryCreateView,
    CategoryDeleteView,
    CategoryListView,
    CategoryUpdateView,
    RecurringTransactionCreateView,
    RecurringTransactionDeleteView,
    RecurringTransactionListView,
    RecurringTransactionUpdateView,
    RestoreTransactionView,
    TransactionCreateView,
    TransactionDeleteView,
    TransactionDetailView,
    TransactionListView,
    TransactionUpdateView,
)


app_name = "transactions"


urlpatterns = [
    # ==================================================
    # Transaction URLs
    # ==================================================

    path(
        "",
        TransactionListView.as_view(),
        name="transaction_list",
    ),

    path(
        "add/",
        TransactionCreateView.as_view(),
        name="transaction_add",
    ),

    path(
        "<int:pk>/",
        TransactionDetailView.as_view(),
        name="transaction_detail",
    ),

    path(
        "<int:pk>/edit/",
        TransactionUpdateView.as_view(),
        name="transaction_update",
    ),

    path(
        "<int:pk>/delete/",
        TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),

    path(
        "<int:pk>/restore/",
        RestoreTransactionView.as_view(),
        name="transaction_restore",
    ),

    # ==================================================
    # Category URLs
    # ==================================================

    path(
        "categories/",
        CategoryListView.as_view(),
        name="category_list",
    ),

    path(
        "categories/add/",
        CategoryCreateView.as_view(),
        name="category_add",
    ),

    path(
        "categories/<int:pk>/edit/",
        CategoryUpdateView.as_view(),
        name="category_update",
    ),

    path(
        "categories/<int:pk>/delete/",
        CategoryDeleteView.as_view(),
        name="category_delete",
    ),

    # ==================================================
    # Recurring Transaction URLs
    # ==================================================

    path(
        "recurring/",
        RecurringTransactionListView.as_view(),
        name="recurring_transaction_list",
    ),

    path(
        "recurring/add/",
        RecurringTransactionCreateView.as_view(),
        name="recurring_transaction_add",
    ),

    path(
        "recurring/<int:pk>/edit/",
        RecurringTransactionUpdateView.as_view(),
        name="recurring_transaction_update",
    ),

    path(
        "recurring/<int:pk>/delete/",
        RecurringTransactionDeleteView.as_view(),
        name="recurring_transaction_delete",
    ),
]