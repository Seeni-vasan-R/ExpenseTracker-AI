from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from transactions.models import Transaction

from budget.models import Budget

from analytics.services import (
    CategoryAnalyticsService,
    DashboardAnalyticsService,
    PatternAnalyticsService,
    TrendAnalyticsService,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Render the authenticated user's dashboard.
    """

    template_name = "dashboard/dashboard.html"
    login_url = "accounts:login"

    def _get_dashboard_budgets(self, user):
        today = timezone.localdate()

        budgets = (
            Budget.objects
            .filter(
                user=user,
                is_active=True,
                start_date__lte=today,
                end_date__gte=today,
            )
            .select_related("category")
            .order_by("-created_at")
        )

        dashboard_budgets = []

        for budget in budgets:
            expense_transactions = Transaction.objects.filter(
                user=user,
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

            spent = (
                expense_transactions.aggregate(
                    total=Sum("amount"),
                ).get("total")
                or Decimal("0.00")
            )

            limit = budget.budget_limit
            remaining = limit - spent

            if limit > 0:
                raw_percentage = (
                    spent / limit
                ) * Decimal("100")
            else:
                raw_percentage = Decimal("0.00")

            percentage = min(
                max(raw_percentage, Decimal("0.00")),
                Decimal("100.00"),
            )

            if spent >= limit:
                status = "Over budget"
                status_class = "over-budget"
            elif raw_percentage >= Decimal("80.00"):
                status = "Almost reached"
                status_class = "almost-reached"
            else:
                status = "On track"
                status_class = "on-track"

            dashboard_budgets.append(
                {
                    "category": (
                        str(budget.category)
                        if budget.category_id
                        else "Monthly budget"
                    ),
                    "spent": spent,
                    "limit": limit,
                    "remaining": remaining,
                    "percentage": percentage,
                    "status": status,
                    "status_class": status_class,
                }
            )

        return dashboard_budgets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        current_date = timezone.localdate()

        month = current_date.month
        year = current_date.year

        summary = (
            DashboardAnalyticsService.get_dashboard_summary(
                user=user,
                month=month,
                year=year,
            )
        )

        budgets = self._get_dashboard_budgets(user)

        recent_transactions = (
            DashboardAnalyticsService.get_recent_activity(
                user=user,
                limit=5,
            )
        )

        category_totals = (
            CategoryAnalyticsService.category_totals(
                user=user,
                month=month,
                year=year,
            )
        )

        top_categories = (
            CategoryAnalyticsService.top_categories(
                user=user,
                month=month,
                year=year,
                limit=5,
            )
        )

        need_want_ratio = (
            CategoryAnalyticsService.need_want_ratio(
                user=user,
                month=month,
                year=year,
            )
        )

        monthly_trend = (
            TrendAnalyticsService.monthly_trend(
                user=user,
                months=6,
            )
        )

        patterns = (
            PatternAnalyticsService.get_all_patterns(
                user=user,
                month=month,
                year=year,
            )
        )

        first_budget = (
            budgets[0]
            if budgets
            else {}
        )

        context.update(
            {
                "current_month": month,
                "current_year": year,

                "summary": summary,
                "income": summary.get(
                    "income",
                    "0.00",
                ),
                "expense": summary.get(
                    "expense",
                    "0.00",
                ),
                "balance": summary.get(
                    "balance",
                    "0.00",
                ),
                "savings": summary.get(
                    "savings",
                    "0.00",
                ),

                "budgets": budgets,
                "budget_overview": budgets,
                "budget_limit": first_budget.get(
                    "limit",
                    "0.00",
                ),
                "budget_remaining": first_budget.get(
                    "remaining",
                    "0.00",
                ),

                "recent_transactions": recent_transactions,
                "category_totals": category_totals,
                "top_categories": top_categories,
                "need_want_ratio": need_want_ratio,
                "monthly_trend": monthly_trend,
                "patterns": patterns,
            }
        )

        return context