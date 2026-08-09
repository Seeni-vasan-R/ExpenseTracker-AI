from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from .forms import BudgetForm
from .models import Budget


class BudgetListView(LoginRequiredMixin, ListView):
    """
    Display budgets belonging only to the authenticated user.
    """

    model = Budget
    template_name = "budgets/budget_list.html"
    context_object_name = "budgets"
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Budget.objects
            .filter(user=self.request.user)
            .select_related("category")
            .order_by("-start_date", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        budgets = self.get_queryset()

        total_budget = (
            budgets.aggregate(total=Sum("budget_limit"))
            .get("total")
            or 0
        )

        active_budget = (
            budgets
            .filter(is_active=True)
            .aggregate(total=Sum("budget_limit"))
            .get("total")
            or 0
        )

        context.update(
            {
                "total_budget": total_budget,
                "active_budget": active_budget,
                "budget_count": budgets.count(),
            }
        )

        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    """
    Create a budget for the authenticated user.
    """

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"
    success_url = reverse_lazy("budgets:budget_list")
    login_url = "accounts:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        with db_transaction.atomic():
            response = super().form_valid(form)

        messages.success(
            self.request,
            "Budget created successfully.",
        )

        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below.",
        )

        return super().form_invalid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update only a budget belonging to the authenticated user.
    """

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"
    success_url = reverse_lazy("budgets:budget_list")
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Budget.objects
            .filter(user=self.request.user)
            .select_related("category")
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        with db_transaction.atomic():
            response = super().form_valid(form)

        messages.success(
            self.request,
            "Budget updated successfully.",
        )

        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below.",
        )

        return super().form_invalid(form)


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete only a budget belonging to the authenticated user.
    """

    model = Budget
    template_name = "budgets/budget_confirm_delete.html"
    success_url = reverse_lazy("budgets:budget_list")
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Budget.objects
            .filter(user=self.request.user)
            .select_related("category")
        )

    def post(self, request, *args, **kwargs):
        budget = self.get_object()

        with db_transaction.atomic():
            budget.delete()

        messages.success(
            request,
            "Budget deleted successfully.",
        )

        return redirect(self.success_url)