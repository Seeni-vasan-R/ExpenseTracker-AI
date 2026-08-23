from collections import defaultdict
from decimal import Decimal

from django.db.models import Count, Sum

from .common import (
    decimal_value,
    get_expense_queryset,
    get_month_bounds,
    money,
    percentage,
)


class CategoryAnalyticsService:
    """
    Category-based expense analytics.

    Only active transactions are included because the shared
    queryset helper uses Transaction.objects.active().
    """

    @classmethod
    def category_totals(
        cls,
        user,
        month,
        year,
    ):
        """
        Return expense totals grouped by category name.
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
            .values(
                "category_id",
                "category__name",
            )
            .annotate(
                total=Sum("amount"),
            )
            .order_by("-total", "category__name")
        )

        totals = {}

        for row in rows:
            category_name = (
                row["category__name"]
                or "Uncategorized"
            )

            totals[category_name] = money(
                row["total"]
            )

        return totals

    @classmethod
    def category_totals_with_counts(
        cls,
        user,
        month,
        year,
    ):
        """
        Return category totals together with transaction counts.
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
            .values(
                "category_id",
                "category__name",
                "category__category_type",
            )
            .annotate(
                total=Sum("amount"),
                transaction_count=Count("id"),
            )
            .order_by("-total", "category__name")
        )

        result = []

        for row in rows:
            result.append(
                {
                    "category_id": row["category_id"],
                    "category": (
                        row["category__name"]
                        or "Uncategorized"
                    ),
                    "category_type": (
                        row["category__category_type"]
                        if row["category_id"]
                        else None
                    ),
                    "total": str(
                        money(row["total"])
                    ),
                    "transaction_count": (
                        row["transaction_count"]
                    ),
                }
            )

        return result

    @classmethod
    def top_categories(
        cls,
        user,
        month,
        year,
        limit=5,
    ):
        """
        Return the largest expense categories.
        """

        limit = max(1, min(int(limit), 50))

        rows = cls.category_totals_with_counts(
            user=user,
            month=month,
            year=year,
        )

        return rows[:limit]

    @classmethod
    def need_want_ratio(
        cls,
        user,
        month,
        year,
    ):
        """
        Compare Need and Want expenses.

        Other category types are returned separately and do
        not get classified as Need or Want.
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
            .values("category__category_type")
            .annotate(total=Sum("amount"))
        )

        totals = defaultdict(lambda: Decimal("0.00"))

        for row in rows:
            category_type = (
                row["category__category_type"]
                or "Unclassified"
            )

            totals[category_type] += decimal_value(
                row["total"]
            )

        need = money(totals["Need"])
        want = money(totals["Want"])
        savings = money(totals["Savings"])
        unclassified = money(totals["Unclassified"])

        classified_expenses = money(
            need
            + want
            + savings
            + unclassified
        )

        return {
            "need": str(need),
            "want": str(want),
            "savings": str(savings),
            "unclassified": str(unclassified),
            "total_expense": str(
                classified_expenses
            ),
            "need_percentage": str(
                percentage(
                    need,
                    classified_expenses,
                )
            ),
            "want_percentage": str(
                percentage(
                    want,
                    classified_expenses,
                )
            ),
            "savings_percentage": str(
                percentage(
                    savings,
                    classified_expenses,
                )
            ),
        }

    @classmethod
    def category_share(
        cls,
        user,
        month,
        year,
    ):
        """
        Return each category's share of total expenses.
        """

        totals = cls.category_totals(
            user=user,
            month=month,
            year=year,
        )

        total_expense = sum(
            totals.values(),
            Decimal("0.00"),
        )

        return {
            category_name: {
                "amount": str(
                    money(amount)
                ),
                "percentage": str(
                    percentage(
                        amount,
                        total_expense,
                    )
                ),
            }
            for category_name, amount in totals.items()
        }

    @classmethod
    def highest_spending_category(
        cls,
        user,
        month,
        year,
    ):
        """
        Return the category with the highest expense.
        """

        rows = cls.top_categories(
            user=user,
            month=month,
            year=year,
            limit=1,
        )

        return rows[0] if rows else None