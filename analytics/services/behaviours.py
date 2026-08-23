from collections import Counter
from decimal import Decimal

from django.db.models import Avg, Count, Max, Sum

from .common import (
    decimal_value,
    get_expense_queryset,
    get_month_bounds,
    money,
    percentage,
)


class BehaviourAnalyticsService:
    """
    Detects simple spending behaviours from active transactions.
    """

    @classmethod
    def get_daily_spending(
        cls,
        user,
        month,
        year,
    ):
        """
        Return expense totals grouped by date.
        """

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        rows = (
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .values("transaction_date")
            .annotate(total=Sum("amount"))
            .order_by("transaction_date")
        )

        return {
            row["transaction_date"].isoformat(): money(
                row["total"]
            )
            for row in rows
        }

    @classmethod
    def get_spending_statistics(
        cls,
        user,
        month,
        year,
    ):
        """
        Return average, maximum, minimum, and count
        for individual expenses.
        """

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        result = (
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .aggregate(
                total=Sum("amount"),
                average=Avg("amount"),
                largest=Max("amount"),
                count=Count("id"),
            )
        )

        total = decimal_value(result["total"])
        average = decimal_value(result["average"])
        largest = decimal_value(result["largest"])

        return {
            "total": str(money(total)),
            "average_transaction": str(
                money(average)
            ),
            "largest_transaction": str(
                money(largest)
            ),
            "transaction_count": result["count"],
        }

    @classmethod
    def get_largest_expenses(
        cls,
        user,
        month,
        year,
        limit=5,
    ):
        """
        Return the largest individual expenses.
        """

        limit = max(1, min(int(limit), 50))

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        transactions = (
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .order_by(
                "-amount",
                "-transaction_date",
            )[:limit]
        )

        return [
            {
                "id": transaction.id,
                "amount": str(
                    money(transaction.amount)
                ),
                "category": (
                    transaction.category.name
                    if transaction.category_id
                    else "Uncategorized"
                ),
                "date": (
                    transaction.transaction_date.isoformat()
                ),
                "description": transaction.description,
            }
            for transaction in transactions
        ]

    @classmethod
    def get_weekday_distribution(
        cls,
        user,
        month,
        year,
    ):
        """
        Group expenses by weekday.
        """

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        rows = get_expense_queryset(
            user=user,
            start_date=start_date,
            end_date=end_date,
        ).values(
            "transaction_date",
            "amount",
        )

        totals = Counter()

        for row in rows:
            transaction_date = row["transaction_date"]
            weekday = transaction_date.strftime("%A")
            totals[weekday] += decimal_value(
                row["amount"]
            )

        weekday_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        return {
            weekday: str(
                money(totals[weekday])
            )
            for weekday in weekday_order
        }

    @classmethod
    def get_category_concentration(
        cls,
        user,
        month,
        year,
        limit=3,
    ):
        """
        Measure how much spending is concentrated in the
        largest categories.
        """

        limit = max(1, min(int(limit), 20))

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        rows = (
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .values(
                "category_id",
                "category__name",
            )
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        category_totals = [
            decimal_value(row["total"])
            for row in rows
        ]

        total_expense = sum(
            category_totals,
            Decimal("0.00"),
        )

        top_amount = sum(
            category_totals[:limit],
            Decimal("0.00"),
        )

        return {
            "top_categories": [
                {
                    "category": (
                        row["category__name"]
                        or "Uncategorized"
                    ),
                    "amount": str(
                        money(row["total"])
                    ),
                }
                for row in rows[:limit]
            ],
            "top_categories_amount": str(
                money(top_amount)
            ),
            "total_expense": str(
                money(total_expense)
            ),
            "concentration_percentage": str(
                percentage(
                    top_amount,
                    total_expense,
                )
            ),
        }

    @classmethod
    def get_all_behaviours(
        cls,
        user,
        month,
        year,
    ):
        """
        Return the complete behaviour payload.
        """

        return {
            "statistics": cls.get_spending_statistics(
                user=user,
                month=month,
                year=year,
            ),
            "largest_expenses": (
                cls.get_largest_expenses(
                    user=user,
                    month=month,
                    year=year,
                )
            ),
            "daily_spending": cls.get_daily_spending(
                user=user,
                month=month,
                year=year,
            ),
            "weekday_distribution": (
                cls.get_weekday_distribution(
                    user=user,
                    month=month,
                    year=year,
                )
            ),
            "category_concentration": (
                cls.get_category_concentration(
                    user=user,
                    month=month,
                    year=year,
                )
            ),
        }


class PatternAnalyticsService(BehaviourAnalyticsService):
    """
    Backward-compatible alias used by views and services.

    This lets existing code call PatternAnalyticsService
    while the implementation remains in behaviours.py.
    """

    @classmethod
    def get_all_patterns(
        cls,
        user,
        month,
        year,
    ):
        return cls.get_all_behaviours(
            user=user,
            month=month,
            year=year,
        )