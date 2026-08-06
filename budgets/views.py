from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Budget
from .forms import BudgetForm


class BudgetListView(LoginRequiredMixin, ListView):
    """
    Display all budgets of the logged-in user.
    """

    model = Budget
    template_name = "budgets/budget_list.html"
    context_object_name = "budgets"
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Budget.objects.filter(
                user=self.request.user
            )
            .select_related("category")
            .order_by("-start_date")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_budget"] = (
            self.get_queryset().aggregate(
                total=Sum("budget_limit")
            )["total"] or 0
        )

        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new budget.
    """

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"

    success_url = reverse_lazy(
        "budgets:budget_list"
    )

    login_url = "accounts:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):

        messages.success(
            self.request,
            "Budget created successfully."
        )

        return super().form_valid(form)

    def form_invalid(self, form):

        messages.error(
            self.request,
            "Please correct the errors below."
        )

        return super().form_invalid(form)
class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing budget.
    """

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"

    success_url = reverse_lazy(
        "budgets:budget_list"
    )

    login_url = "accounts:login"

    def get_queryset(self):
        return Budget.objects.filter(
            user=self.request.user
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):

        messages.success(
            self.request,
            "Budget updated successfully."
        )

        return super().form_valid(form)

    def form_invalid(self, form):

        messages.error(
            self.request,
            "Please correct the errors below."
        )

        return super().form_invalid(form)


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a budget.
    """

    model = Budget

    success_url = reverse_lazy(
        "budgets:budget_list"
    )

    login_url = "accounts:login"

    def get_queryset(self):
        return Budget.objects.filter(
            user=self.request.user
        )

    def post(self, request, *args, **kwargs):

        budget = self.get_object()

        budget.delete()

        messages.success(
            request,
            "Budget deleted successfully."
        )

        return redirect(self.success_url)