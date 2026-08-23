from calendar import monthrange
from collections import defaultdict
from datetime import date

from django.db.models import Count, Sum

from .common import (
    decimal_value,
    get_expense_queryset,
    get_income_queryset,
    get_month_bounds,
    money,
)


class TransactionAnalyticsService:
    @classmethod
    def monthly_expense(
        cls,
        user,
        month,
        year,
    ):
        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        total = (
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .aggregate(total=Sum("amount"))
            ["total"]
        )

        return money(
            decimal_value(total)
        )

    @classmethod
    def monthly_income(
        cls,
        user,
        month,
        year,
    ):
        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        total = (
            get_income_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .aggregate(total=Sum("amount"))
            ["total"]
        )

        return money(
            decimal_value(total)
        )

    @classmethod
    def income_vs_expense(
        cls,
        user,
        month,
        year,
    ):
        income = cls.monthly_income(
            user=user,
            month=month,
            year=year,
        )

        expense = cls.monthly_expense(
            user=user,
            month=month,
            year=year,
        )

        return {
            "month": month,
            "year": year,
            "income": str(income),
            "expense": str(expense),
            "balance": str(
                money(income - expense)
            ),
        }

    @classmethod
    def daily_spending(
        cls,
        user,
        start_date,
        end_date,
    ):
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
            row["transaction_date"].isoformat(): str(
                money(row["total"])
            )
            for row in rows
        }

    @classmethod
    def daily_income_expense_timeline(
        cls,
        user,
        month,
        year,
    ):
        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        income_rows = (
            get_income_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .values("transaction_date")
            .annotate(total=Sum("amount"))
            .order_by("transaction_date")
        )

        expense_rows = (
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
            .values("transaction_date")
            .annotate(total=Sum("amount"))
            .order_by("transaction_date")
        )

        income_by_date = defaultdict(float)

        for row in income_rows:
            income_by_date[
                row["transaction_date"]
            ] = float(
                money(row["total"])
            )

        expense_by_date = defaultdict(float)

        for row in expense_rows:
            expense_by_date[
                row["transaction_date"]
            ] = float(
                money(row["total"])
            )

        days_in_month = monthrange(
            year,
            month,
        )[1]

        labels = []
        income_values = []
        expense_values = []
        balance_values = []

        for day in range(1, days_in_month + 1):
            current_date = date(
                year,
                month,
                day,
            )

            income = income_by_date[current_date]
            expense = expense_by_date[current_date]

            labels.append(
                current_date.isoformat()
            )

            income_values.append(income)
            expense_values.append(expense)
            balance_values.append(
                income - expense
            )

        return {
            "month": month,
            "year": year,
            "labels": labels,
            "income": income_values,
            "expense": expense_values,
            "balance": balance_values,
        }

    @classmethod
    def monthly_expense_calendar(
        cls,
        user,
        month,
        year,
    ):
        """
        Return every date in the selected month, including
        zero-expense days, for the expense calendar heatmap.
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
            .annotate(
                total=Sum("amount"),
                transaction_count=Count("id"),
            )
            .order_by("transaction_date")
        )

        expenses_by_date = {}

        for row in rows:
            expenses_by_date[
                row["transaction_date"]
            ] = {
                "expense": money(row["total"]),
                "transaction_count": (
                    row["transaction_count"]
                ),
            }

        days_in_month = monthrange(
            year,
            month,
        )[1]

        days = []

        for day in range(1, days_in_month + 1):
            current_date = date(
                year,
                month,
                day,
            )

            values = expenses_by_date.get(
                current_date,
                {
                    "expense": money(0),
                    "transaction_count": 0,
                },
            )

            days.append(
                {
                    "date": current_date.isoformat(),
                    "expense": str(values["expense"]),
                    "transaction_count": (
                        values["transaction_count"]
                    ),
                }
            )

        return {
            "month": month,
            "year": year,
            "days": days,
        }