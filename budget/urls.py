from django.urls import path

from .views import (
    BudgetCreateView,
    BudgetDeleteView,
    BudgetListView,
    BudgetUpdateView,
)


app_name = "budget"


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