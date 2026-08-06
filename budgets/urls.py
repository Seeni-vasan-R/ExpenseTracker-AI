from django.urls import path

from .views import (
    BudgetListView,
    BudgetCreateView,
    BudgetUpdateView,
    BudgetDeleteView,
)

app_name = "budgets"

urlpatterns = [

    path(
        "",
        BudgetListView.as_view(),
        name="budget_list",
    ),

    path(
        "add/",
        BudgetCreateView.as_view(),
        name="budget_add",
    ),

    path(
        "<int:pk>/edit/",
        BudgetUpdateView.as_view(),
        name="budget_update",
    ),

    path(
        "<int:pk>/delete/",
        BudgetDeleteView.as_view(),
        name="budget_delete",
    ),

]