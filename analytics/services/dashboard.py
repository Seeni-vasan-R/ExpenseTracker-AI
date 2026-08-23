from datetime import date
from decimal import Decimal

from django.db.models import Count, Max, Min, Sum
from django.utils import timezone

from .common import (
    decimal_value,
    get_expense_queryset,
    get_income_queryset,
    get_month_bounds,
    money,
    percentage,
    signed_balance,
)


class DashboardAnalyticsService:
    """
    Provides the main data displayed on the Analytics dashboard.
    """

    @classmethod
    def get_dashboard_summary(
        cls,
        user,
        month=None,
        year=None,
    ):
        """
        Return income, expenses, balance, and savings
        metrics for a selected month.
        """

        today = timezone.localdate()

        if month is None:
            month = today.month

        if year is None:
            year = today.year

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        income_queryset = get_income_queryset(
            user=user,
            start_date=start_date,
            end_date=end_date,
        )

        expense_queryset = get_expense_queryset(
            user=user,
            start_date=start_date,
            end_date=end_date,
        )

        income = decimal_value(
            income_queryset.aggregate(
                total=Sum("amount"),
            )["total"]
        )

        expense = decimal_value(
            expense_queryset.aggregate(
                total=Sum("amount"),
            )["total"]
        )

        balance = signed_balance(
            income=income,
            expense=expense,
        )

        savings_rate = percentage(
            part=balance,
            whole=income,
        )

        transaction_count = (
            income_queryset.count()
            + expense_queryset.count()
        )

        return {
            "month": month,
            "year": year,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "income": str(money(income)),
            "expense": str(money(expense)),
            "balance": str(balance),
            "savings_rate": str(savings_rate),
            "transaction_count": transaction_count,
        }

    @classmethod
    def get_recent_activity(
        cls,
        user,
        limit=10,
    ):
        """
        Return the user's latest active transactions.
        """

        limit = max(1, min(int(limit), 100))

        from transactions.models import Transaction

        return list(
            Transaction.objects
            .active()
            .filter(user=user)
            .select_related("category")
            .order_by(
                "-transaction_date",
                "-created_at",
            )[:limit]
        )

    @classmethod
    def get_month_summary(
        cls,
        user,
        month,
        year,
    ):
        """
        Return a compact monthly summary suitable for
        charts, snapshots, and AI Summary.
        """

        summary = cls.get_dashboard_summary(
            user=user,
            month=month,
            year=year,
        )

        return {
            "period": f"{year:04d}-{month:02d}",
            "income": summary["income"],
            "expense": summary["expense"],
            "balance": summary["balance"],
            "savings_rate": summary["savings_rate"],
            "transaction_count": (
                summary["transaction_count"]
            ),
        }

    @classmethod
    def get_month_comparison(
        cls,
        user,
        month,
        year,
    ):
        """
        Compare the selected month with the previous month.
        """

        current_month = cls.get_dashboard_summary(
            user=user,
            month=month,
            year=year,
        )

        if month == 1:
            previous_month = 12
            previous_year = year - 1
        else:
            previous_month = month - 1
            previous_year = year

        previous = cls.get_dashboard_summary(
            user=user,
            month=previous_month,
            year=previous_year,
        )

        current_income = Decimal(
            current_month["income"]
        )
        previous_income = Decimal(
            previous["income"]
        )

        current_expense = Decimal(
            current_month["expense"]
        )
        previous_expense = Decimal(
            previous["expense"]
        )

        current_balance = Decimal(
            current_month["balance"]
        )
        previous_balance = Decimal(
            previous["balance"]
        )

        return {
            "current": current_month,
            "previous": previous,
            "income_change": str(
                money(
                    current_income
                    - previous_income
                )
            ),
            "expense_change": str(
                money(
                    current_expense
                    - previous_expense
                )
            ),
            "balance_change": str(
                money(
                    current_balance
                    - previous_balance
                )
            ),
            "income_change_percentage": str(
                percentage(
                    current_income
                    - previous_income,
                    previous_income,
                )
            ),
            "expense_change_percentage": str(
                percentage(
                    current_expense
                    - previous_expense,
                    previous_expense,
                )
            ),
        }

    @classmethod
    def get_transaction_counts(
        cls,
        user,
        month,
        year,
    ):
        """
        Return transaction counts for the selected month.
        """

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        income_queryset = get_income_queryset(
            user=user,
            start_date=start_date,
            end_date=end_date,
        )

        expense_queryset = get_expense_queryset(
            user=user,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "income_count": income_queryset.count(),
            "expense_count": expense_queryset.count(),
            "total_count": (
                income_queryset.count()
                + expense_queryset.count()
            ),
        }

    @classmethod
    def get_largest_expense(
        cls,
        user,
        month,
        year,
    ):
        """
        Return the largest active expense for a month.
        """

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        transaction = (
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .order_by(
                "-amount",
                "-transaction_date",
            )
            .first()
        )

        if transaction is None:
            return None

        return {
            "id": transaction.id,
            "amount": str(
                money(transaction.amount)
            ),
            "category": (
                transaction.category.name
                if transaction.category_id
                else None
            ),
            "date": (
                transaction.transaction_date.isoformat()
            ),
            "description": transaction.description,
        }

    @classmethod
    def get_active_date_range(cls, user):
        """
        Return the date range covered by active transactions.
        """

        from transactions.models import Transaction

        result = (
            Transaction.objects
            .active()
            .filter(user=user)
            .aggregate(
                earliest_date=Min(
                    "transaction_date",
                ),
                latest_date=Max(
                    "transaction_date",
                ),
            )
        )

        return {
            "earliest_date": (
                result["earliest_date"].isoformat()
                if result["earliest_date"]
                else None
            ),
            "latest_date": (
                result["latest_date"].isoformat()
                if result["latest_date"]
                else None
            ),
        }