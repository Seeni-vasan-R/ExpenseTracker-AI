from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from budget.models import Budget
from transactions.models import Transaction


ZERO = Decimal("0.00")


def _sum_amount(queryset):
    return (
        queryset.aggregate(
            total=Sum("amount", default=ZERO)
        ).get("total")
        or ZERO
    )


def _month_range(year, month):
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    return start_date, end_date


class DashboardAnalyticsService:
    """
    Basic dashboard calculations.

    This is a temporary implementation until the analytics module
    is completed.
    """

    @staticmethod
    def get_dashboard_summary(user, month, year):
        start_date, end_date = _month_range(year, month)

        transactions = Transaction.objects.active().filter(
            user=user,
            transaction_date__range=(start_date, end_date),
        )

        income = _sum_amount(
            transactions.filter(transaction_type="Income")
        )

        expense = _sum_amount(
            transactions.filter(transaction_type="Expense")
        )

        balance = income - expense

        return {
            "income": income,
            "expense": expense,
            "balance": balance,
            "savings": balance,
        }

    @staticmethod
    def get_budget_status(user):
        today = timezone.localdate()

        budgets = (
            Budget.objects.filter(
                user=user,
                is_active=True,
                start_date__lte=today,
                end_date__gte=today,
            )
            .select_related("category")
            .order_by("end_date", "category__name")
        )

        budget_status = []

        for budget in budgets:
            expenses = Transaction.objects.active().filter(
                user=user,
                transaction_type="Expense",
                transaction_date__range=(
                    budget.start_date,
                    budget.end_date,
                ),
            )

            if budget.category_id:
                expenses = expenses.filter(
                    category_id=budget.category_id
                )

            spent = _sum_amount(expenses)
            remaining = budget.budget_limit - spent

            budget_status.append(
                {
                    "id": budget.id,
                    "category": (
                        budget.category.name
                        if budget.category_id
                        else "Overall"
                    ),
                    "limit": budget.budget_limit,
                    "spent": spent,
                    "remaining": remaining,
                    "start_date": budget.start_date,
                    "end_date": budget.end_date,
                    "is_exceeded": remaining < ZERO,
                }
            )

        return budget_status

    @staticmethod
    def get_recent_activity(user, limit=5):
        return list(
            Transaction.objects.active()
            .filter(user=user)
            .select_related("category")
            .order_by(
                "-transaction_date",
                "-created_at",
            )[:limit]
        )


class CategoryAnalyticsService:
    """
    Basic category-level expense calculations.
    """

    @staticmethod
    def _monthly_expenses(user, month, year):
        start_date, end_date = _month_range(year, month)

        return (
            Transaction.objects.active()
            .filter(
                user=user,
                transaction_type="Expense",
                transaction_date__range=(
                    start_date,
                    end_date,
                ),
            )
            .select_related("category")
        )

    @staticmethod
    def category_totals(user, month, year):
        expenses = CategoryAnalyticsService._monthly_expenses(
            user=user,
            month=month,
            year=year,
        )

        totals = {}

        for transaction in expenses:
            category_name = (
                transaction.category.name
                if transaction.category_id
                else "Uncategorized"
            )

            totals[category_name] = (
                totals.get(category_name, ZERO)
                + transaction.amount
            )

        return [
            {
                "category": category,
                "total": total,
            }
            for category, total in sorted(
                totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

    @staticmethod
    def top_categories(user, month, year, limit=5):
        totals = CategoryAnalyticsService.category_totals(
            user=user,
            month=month,
            year=year,
        )

        return totals[:limit]

    @staticmethod
    def need_want_ratio(user, month, year):
        expenses = CategoryAnalyticsService._monthly_expenses(
            user=user,
            month=month,
            year=year,
        )

        need_total = ZERO
        want_total = ZERO
        savings_total = ZERO
        other_total = ZERO

        for transaction in expenses:
            category_type = transaction.category.category_type

            if category_type == "Need":
                need_total += transaction.amount
            elif category_type == "Want":
                want_total += transaction.amount
            elif category_type == "Savings":
                savings_total += transaction.amount
            else:
                other_total += transaction.amount

        total = (
            need_total
            + want_total
            + savings_total
            + other_total
        )

        return {
            "need": need_total,
            "want": want_total,
            "savings": savings_total,
            "other": other_total,
            "total": total,
        }


class TrendAnalyticsService:
    """
    Basic monthly income and expense trend.
    """

    @staticmethod
    def monthly_trend(user, months=6):
        today = timezone.localdate()
        current_month = today.replace(day=1)

        trend = []

        for offset in range(months - 1, -1, -1):
            month_date = current_month - relativedelta(
                months=offset
            )

            start_date, end_date = _month_range(
                month_date.year,
                month_date.month,
            )

            transactions = Transaction.objects.active().filter(
                user=user,
                transaction_date__range=(
                    start_date,
                    end_date,
                ),
            )

            income = _sum_amount(
                transactions.filter(transaction_type="Income")
            )

            expense = _sum_amount(
                transactions.filter(transaction_type="Expense")
            )

            trend.append(
                {
                    "month": month_date.strftime("%b %Y"),
                    "year": month_date.year,
                    "month_number": month_date.month,
                    "income": income,
                    "expense": expense,
                    "balance": income - expense,
                }
            )

        return trend


class PatternAnalyticsService:
    """
    Temporary placeholder for behavioural pattern analysis.

    The final implementation can later use Isolation Forest,
    Decision Trees, and other analytics logic.
    """

    @staticmethod
    def get_all_patterns(user, month, year):
        return []