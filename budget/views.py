from decimal import Decimal

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

from transactions.models import Transaction

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

    def _add_budget_metrics(self, budgets):
        for budget in budgets:
            expense_transactions = Transaction.objects.filter(
                user=self.request.user,
                transaction_type="Expense",
                transaction_date__range=(
                    budget.start_date,
                    budget.end_date,
                ),
            )

            if budget.category_id:
                expense_transactions = (
                    expense_transactions.filter(
                        category_id=budget.category_id,
                    )
                )

            used_amount = (
                expense_transactions.aggregate(
                    total=Sum("amount"),
                ).get("total")
                or Decimal("0.00")
            )

            remaining_amount = (
                budget.budget_limit - used_amount
            )

            if budget.budget_limit > 0:
                raw_progress = (
                    used_amount / budget.budget_limit
                ) * Decimal("100")
            else:
                raw_progress = Decimal("0.00")

            progress_percentage = min(
                max(raw_progress, Decimal("0.00")),
                Decimal("100.00"),
            )

            if used_amount >= budget.budget_limit:
                budget.status = "Over budget"
                budget.status_class = "over-budget"
            elif raw_progress >= Decimal("80"):
                budget.status = "Almost reached"
                budget.status_class = "almost-reached"
            else:
                budget.status = "On track"
                budget.status_class = "on-track"

            budget.used_amount = used_amount
            budget.remaining_amount = remaining_amount
            budget.progress_percentage = (
                progress_percentage
            )
            budget.raw_progress_percentage = (
                raw_progress
            )

        return budgets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        budgets = list(self.get_queryset())
        budgets = self._add_budget_metrics(budgets)

        total_budget = sum(
            (
                budget.budget_limit
                for budget in budgets
            ),
            Decimal("0.00"),
        )

        active_budgets = [
            budget
            for budget in budgets
            if budget.is_active
        ]

        active_budget = sum(
            (
                budget.budget_limit
                for budget in active_budgets
            ),
            Decimal("0.00"),
        )

        total_used = sum(
            (
                budget.used_amount
                for budget in budgets
            ),
            Decimal("0.00"),
        )

        context.update(
            {
                "budgets": budgets,
                "total_budget": total_budget,
                "active_budget": active_budget,
                "total_used": total_used,
                "budget_count": len(budgets),
                "active_budget_count": len(
                    active_budgets
                ),
                "budget_limit_per_month": (
                    Budget.MAX_ACTIVE_BUDGETS_PER_MONTH
                ),
            }
        )

        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    """
    Create a monthly budget for the authenticated user.
    """

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"
    success_url = reverse_lazy(
        "budget:budget_list"
    )
    login_url = "accounts:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.is_active = True

        try:
            with db_transaction.atomic():
                response = super().form_valid(form)
        except Exception as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)

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
    Update only a budget belonging to the
    authenticated user.
    """

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"
    success_url = reverse_lazy(
        "budget:budget_list"
    )
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

        try:
            with db_transaction.atomic():
                response = super().form_valid(form)
        except Exception as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)

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
    Delete only a budget belonging to the
    authenticated user.
    """

    model = Budget
    template_name = (
        "budgets/budget_confirm_delete.html"
    )
    success_url = reverse_lazy(
        "budget:budget_list"
    )
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