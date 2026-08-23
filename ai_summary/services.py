from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from analytics.services.behaviours import (
    BehaviourAnalyticsService,
)
from analytics.services.budgets import (
    BudgetAnalyticsService,
)
from analytics.services.categories import (
    CategoryAnalyticsService,
)
from analytics.services.dashboard import (
    DashboardAnalyticsService,
)
from analytics.services.trends import (
    TrendAnalyticsService,
)

from .models import AISummary


def decimal_value(value):
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value))


def currency(value):
    return f"₹{decimal_value(value):,.2f}"


def percentage(value):
    return f"{decimal_value(value):,.2f}%"


def make_json_safe(value):
    """
    Converts values produced by analytics services into types that
    can be stored safely in Django JSONField instances.

    Decimal values are converted to strings to preserve financial
    precision. The frontend already converts them back to numbers
    when it displays charts and metric values.
    """

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    return value


class AISummaryService:
    """
    Generates explainable financial insights from Analytics data.

    This is a deterministic local summary engine. It does not
    send user data to an external AI provider.
    """

    @classmethod
    def get_period(
        cls,
        month=None,
        year=None,
    ):
        today = timezone.localdate()

        return (
            int(month or today.month),
            int(year or today.year),
        )

    @classmethod
    def collect_metrics(
        cls,
        user,
        month=None,
        year=None,
    ):
        month, year = cls.get_period(
            month=month,
            year=year,
        )

        summary = (
            DashboardAnalyticsService
            .get_dashboard_summary(
                user=user,
                month=month,
                year=year,
            )
        )

        category_totals = (
            CategoryAnalyticsService
            .category_totals_with_counts(
                user=user,
                month=month,
                year=year,
            )
        )

        need_want = (
            CategoryAnalyticsService
            .need_want_ratio(
                user=user,
                month=month,
                year=year,
            )
        )

        budgets = (
            BudgetAnalyticsService
            .budget_overview(
                user=user,
                month=month,
                year=year,
            )
        )

        behaviours = (
            BehaviourAnalyticsService
            .get_all_behaviours(
                user=user,
                month=month,
                year=year,
            )
        )

        comparison = (
            DashboardAnalyticsService
            .get_month_comparison(
                user=user,
                month=month,
                year=year,
            )
        )

        trend = (
            TrendAnalyticsService
            .monthly_income_expense(
                user=user,
                months=6,
            )
        )

        return {
            "month": month,
            "year": year,
            "summary": summary,
            "category_totals": category_totals,
            "need_want": need_want,
            "budgets": budgets,
            "behaviours": behaviours,
            "comparison": comparison,
            "trend": trend,
        }

    @classmethod
    def generate_insights(cls, metrics):
        summary = metrics["summary"]
        categories = metrics["category_totals"]
        budgets = metrics["budgets"]
        need_want = metrics["need_want"]
        behaviours = metrics["behaviours"]
        comparison = metrics["comparison"]

        insights = []

        income = decimal_value(
            summary.get("income")
        )

        expense = decimal_value(
            summary.get("expense")
        )

        balance = decimal_value(
            summary.get("balance")
        )

        previous_expense = decimal_value(
            comparison.get(
                "previous",
                {},
            ).get("expense")
        )

        expense_change = decimal_value(
            comparison.get(
                "expense_change_percentage"
            )
        )

        if income == 0 and expense > 0:
            insights.append(
                {
                    "type": "warning",
                    "title": (
                        "Expenses without recorded income"
                    ),
                    "message": (
                        "This month has expenses but no recorded "
                        "income. Add all income sources for a more "
                        "accurate financial picture."
                    ),
                }
            )

        elif balance > 0:
            insights.append(
                {
                    "type": "positive",
                    "title": "Positive monthly balance",
                    "message": (
                        f"You finished the month with "
                        f"{currency(balance)} left after expenses."
                    ),
                }
            )

        elif balance < 0:
            insights.append(
                {
                    "type": "warning",
                    "title": "Negative monthly balance",
                    "message": (
                        f"Expenses exceeded recorded income by "
                        f"{currency(abs(balance))}."
                    ),
                }
            )

        if previous_expense > 0 and expense_change > 10:
            insights.append(
                {
                    "type": "warning",
                    "title": "Expenses increased",
                    "message": (
                        f"Expenses are up by "
                        f"{percentage(expense_change)} "
                        "compared with the previous month."
                    ),
                }
            )

        elif previous_expense > 0 and expense_change < -10:
            insights.append(
                {
                    "type": "positive",
                    "title": "Expenses decreased",
                    "message": (
                        f"Expenses are down by "
                        f"{percentage(abs(expense_change))} "
                        "compared with the previous month."
                    ),
                }
            )

        if categories:
            largest = categories[0]

            largest_total = decimal_value(
                largest.get("total")
            )

            total_expense = expense

            if total_expense > 0:
                share = (
                    largest_total
                    / total_expense
                    * Decimal("100")
                )

                if share >= 40:
                    insights.append(
                        {
                            "type": "neutral",
                            "title": (
                                "High category concentration"
                            ),
                            "message": (
                                f"{largest.get('category', 'This category')} "
                                f"accounts for {percentage(share)} "
                                "of your expenses."
                            ),
                        }
                    )

        need_percentage = decimal_value(
            need_want.get("need_percentage")
        )

        want_percentage = decimal_value(
            need_want.get("want_percentage")
        )

        if want_percentage > 40:
            insights.append(
                {
                    "type": "warning",
                    "title": (
                        "Wants are a large expense share"
                    ),
                    "message": (
                        f"Wants represent "
                        f"{percentage(want_percentage)} "
                        "of classified spending this month."
                    ),
                }
            )

        if need_percentage > 70:
            insights.append(
                {
                    "type": "neutral",
                    "title": "Needs dominate spending",
                    "message": (
                        f"Needs represent "
                        f"{percentage(need_percentage)} "
                        "of classified spending."
                    ),
                }
            )

        over_budget = [
            budget
            for budget in budgets.get("budgets", [])
            if budget.get("is_over_budget")
        ]

        if over_budget:
            names = ", ".join(
                budget.get(
                    "category",
                    "Overall budget",
                )
                for budget in over_budget
            )

            insights.append(
                {
                    "type": "warning",
                    "title": "Budget limit exceeded",
                    "message": (
                        f"You exceeded these budget limits: {names}."
                    ),
                }
            )

        largest_expenses = behaviours.get(
            "largest_expenses",
            [],
        )

        if largest_expenses:
            largest_transaction = largest_expenses[0]

            insights.append(
                {
                    "type": "neutral",
                    "title": "Largest individual expense",
                    "message": (
                        f"Your largest expense was "
                        f"{currency(largest_transaction.get('amount'))} "
                        f"for "
                        f"{largest_transaction.get('category', 'an uncategorized transaction')}."
                    ),
                }
            )

        if not insights:
            insights.append(
                {
                    "type": "neutral",
                    "title": "Not enough data yet",
                    "message": (
                        "Add more transactions to generate "
                        "personalized insights."
                    ),
                }
            )

        return insights

    @classmethod
    def generate_recommendations(cls, metrics):
        summary = metrics["summary"]
        budgets = metrics["budgets"]
        need_want = metrics["need_want"]
        behaviours = metrics["behaviours"]

        recommendations = []

        income = decimal_value(
            summary.get("income")
        )

        expense = decimal_value(
            summary.get("expense")
        )

        balance = decimal_value(
            summary.get("balance")
        )

        want_percentage = decimal_value(
            need_want.get("want_percentage")
        )

        alerts = [
            budget
            for budget in budgets.get("budgets", [])
            if budget.get("status")
            in {
                "near_limit",
                "at_limit",
                "over_budget",
            }
        ]

        if balance < 0:
            recommendations.append(
                {
                    "priority": "high",
                    "title": (
                        "Reduce discretionary spending"
                    ),
                    "message": (
                        "Review wants and non-essential expenses "
                        "before adding new commitments."
                    ),
                }
            )

        if income > 0 and balance > 0:
            savings_rate = (
                balance / income * Decimal("100")
            )

            if savings_rate < 20:
                recommendations.append(
                    {
                        "priority": "medium",
                        "title": (
                            "Increase your savings rate"
                        ),
                        "message": (
                            "Your current surplus is below 20% of "
                            "recorded income. Consider setting aside "
                            "a fixed amount immediately after payday."
                        ),
                    }
                )

        if want_percentage > 35:
            recommendations.append(
                {
                    "priority": "medium",
                    "title": "Set a wants spending cap",
                    "message": (
                        "Create a separate limit for shopping, "
                        "entertainment, and other discretionary "
                        "categories."
                    ),
                }
            )

        if alerts:
            recommendations.append(
                {
                    "priority": "high",
                    "title": "Review budget alerts",
                    "message": (
                        "At least one budget is near or above its "
                        "limit. Check the budget breakdown before "
                        "making additional purchases."
                    ),
                }
            )

        statistics = behaviours.get(
            "statistics",
            {},
        )

        average_transaction = decimal_value(
            statistics.get("average_transaction")
        )

        largest_transaction = decimal_value(
            statistics.get("largest_transaction")
        )

        if (
            average_transaction > 0
            and largest_transaction
            >= average_transaction * Decimal("5")
        ):
            recommendations.append(
                {
                    "priority": "medium",
                    "title": (
                        "Review large one-off expenses"
                    ),
                    "message": (
                        "A large transaction is significantly above "
                        "your average expense. Consider planning "
                        "similar purchases in advance."
                    ),
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "priority": "low",
                    "title": "Keep your current routine",
                    "message": (
                        "Your current data does not show a major "
                        "warning. Continue recording transactions "
                        "consistently."
                    ),
                }
            )

        return recommendations

    @classmethod
    def build_summary_text(cls, metrics, insights):
        summary = metrics["summary"]

        month = metrics["month"]
        year = metrics["year"]

        income = decimal_value(
            summary.get("income")
        )

        expense = decimal_value(
            summary.get("expense")
        )

        balance = decimal_value(
            summary.get("balance")
        )

        if income > 0:
            savings_rate = (
                balance / income * Decimal("100")
            )
        else:
            savings_rate = Decimal("0.00")

        return (
            f"For {month:02d}/{year}, you recorded "
            f"{currency(income)} in income and "
            f"{currency(expense)} in expenses. "
            f"Your resulting balance was "
            f"{currency(balance)}, with an estimated savings "
            f"rate of {percentage(savings_rate)}. "
            f"The analysis identified {len(insights)} "
            "notable financial signal(s)."
        )

    @classmethod
    @transaction.atomic
    def generate(
        cls,
        user,
        month=None,
        year=None,
        save=True,
    ):
        metrics = cls.collect_metrics(
            user=user,
            month=month,
            year=year,
        )

        insights = cls.generate_insights(
            metrics
        )

        recommendations = (
            cls.generate_recommendations(
                metrics
            )
        )

        summary_text = cls.build_summary_text(
            metrics=metrics,
            insights=insights,
        )

        serialized_metrics = make_json_safe(
            {
                "summary": metrics["summary"],
                "category_totals": (
                    metrics["category_totals"]
                ),
                "need_want": metrics["need_want"],
                "budgets": metrics["budgets"],
                "behaviours": metrics["behaviours"],
                "comparison": metrics["comparison"],
                "trend": metrics["trend"],
            }
        )

        payload = make_json_safe(
            {
                "month": metrics["month"],
                "year": metrics["year"],
                "summary_text": summary_text,
                "insights": insights,
                "recommendations": recommendations,
                "metrics": serialized_metrics,
            }
        )

        if not save:
            return payload

        summary, _ = AISummary.objects.update_or_create(
            user=user,
            month=metrics["month"],
            year=metrics["year"],
            defaults={
                "summary_text": summary_text,
                "insights": make_json_safe(insights),
                "recommendations": make_json_safe(
                    recommendations
                ),
                "metrics": serialized_metrics,
            },
        )

        payload["id"] = summary.id
        payload["created_at"] = (
            summary.created_at.isoformat()
        )
        payload["updated_at"] = (
            summary.updated_at.isoformat()
        )

        return payload

    @classmethod
    def latest(
        cls,
        user,
    ):
        return (
            AISummary.objects
            .filter(user=user)
            .first()
        )