from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from transactions.models import Transaction
from budgets.models import Budget


class DashboardView(LoginRequiredMixin, TemplateView):

    template_name = "dashboard/dashboard.html"
    login_url = "accounts:login"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        user = self.request.user
        today = timezone.now().date()

        transactions = (
            Transaction.objects.active()
            .filter(user=user)
            .select_related("category")
        )

        income = (
            transactions.filter(
                transaction_type="Income"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        expense = (
            transactions.filter(
                transaction_type="Expense"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        current_month = today.month
        current_year = today.year

        monthly_income = (
            transactions.filter(
                transaction_type="Income",
                transaction_date__month=current_month,
                transaction_date__year=current_year,
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        monthly_expense = (
            transactions.filter(
                transaction_type="Expense",
                transaction_date__month=current_month,
                transaction_date__year=current_year,
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        active_budget = (
            Budget.objects.filter(
                user=user,
                is_active=True,
            ).order_by("-start_date").first()
        )

        budget_limit = (
            active_budget.budget_limit
            if active_budget
            else 0
        )

        budget_remaining = (
            budget_limit - monthly_expense
            if budget_limit
            else 0
        )

        recent_transactions = (
            transactions.order_by(
                "-transaction_date",
                "-created_at",
            )[:5]
        )

        context["balance"] = income - expense
        context["income"] = income
        context["expense"] = expense

        context["monthly_income"] = monthly_income
        context["monthly_expense"] = monthly_expense

        context["budget_limit"] = budget_limit
        context["budget_remaining"] = budget_remaining

        context["recent_transactions"] = recent_transactions

        return context