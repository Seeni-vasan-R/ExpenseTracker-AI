from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from analytics.services import (
    CategoryAnalyticsService,
    DashboardAnalyticsService,
    PatternAnalyticsService,
    TrendAnalyticsService,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Render the authenticated user's dashboard.

    Financial calculations are delegated to the analytics services.
    """

    template_name = "dashboard/dashboard.html"
    login_url = "accounts:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        current_date = timezone.localdate()

        month = current_date.month
        year = current_date.year

        summary = DashboardAnalyticsService.get_dashboard_summary(
            user=user,
            month=month,
            year=year,
        )

        budgets = DashboardAnalyticsService.get_budget_status(
            user=user,
        )

        recent_transactions = (
            DashboardAnalyticsService.get_recent_activity(
                user=user,
                limit=5,
            )
        )

        category_totals = CategoryAnalyticsService.category_totals(
            user=user,
            month=month,
            year=year,
        )

        top_categories = CategoryAnalyticsService.top_categories(
            user=user,
            month=month,
            year=year,
            limit=5,
        )

        need_want_ratio = CategoryAnalyticsService.need_want_ratio(
            user=user,
            month=month,
            year=year,
        )

        monthly_trend = TrendAnalyticsService.monthly_trend(
            user=user,
            months=6,
        )

        patterns = PatternAnalyticsService.get_all_patterns(
            user=user,
            month=month,
            year=year,
        )

        first_budget = budgets[0] if budgets else {}

        context.update(
            {
                "current_month": month,
                "current_year": year,

                "summary": summary,
                "income": summary.get("income", "0"),
                "expense": summary.get("expense", "0"),
                "balance": summary.get("balance", "0"),
                "savings": summary.get("savings", "0"),

                "budgets": budgets,
                "budget_overview": budgets,
                "budget_limit": first_budget.get("limit", "0"),
                "budget_remaining": first_budget.get(
                    "remaining",
                    "0",
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