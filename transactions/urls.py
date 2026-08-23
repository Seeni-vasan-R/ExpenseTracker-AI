from django.urls import path

from .views import (
    CategoryCreateView,
    CategoryDeleteView,
    CategoryListView,
    CategoryUpdateView,
    RestoreTransactionView,
    TransactionCreateView,
    TransactionDeleteView,
    TransactionDetailView,
    TransactionListView,
    TransactionUpdateView,
)


app_name = "transactions"


urlpatterns = [
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
        name="transaction_edit",
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
        name="category_edit",
    ),
    path(
        "categories/<int:pk>/delete/",
        CategoryDeleteView.as_view(),
        name="category_delete",
    ),
]