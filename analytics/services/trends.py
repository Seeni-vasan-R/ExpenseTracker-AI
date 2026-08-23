from datetime import date
from decimal import Decimal

from django.db.models import Sum

from .common import (
    decimal_value,
    get_expense_queryset,
    get_income_queryset,
    get_month_bounds,
    money,
    month_key,
    percentage,
)


class TrendAnalyticsService:
    """
    Calculates historical income and expense trends.
    """

    @staticmethod
    def _previous_month(month, year):
        if month == 1:
            return 12, year - 1

        return month - 1, year

    @classmethod
    def _month_totals(
        cls,
        user,
        month,
        year,
    ):
        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        income = decimal_value(
            get_income_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            ).aggregate(
                total=Sum("amount"),
            )["total"]
        )

        expense = decimal_value(
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            ).aggregate(
                total=Sum("amount"),
            )["total"]
        )

        return {
            "month": month,
            "year": year,
            "period": month_key(month, year),
            "income": money(income),
            "expense": money(expense),
            "balance": money(income - expense),
        }

    @classmethod
    def _periods_ending_with(
        cls,
        month,
        year,
        months,
    ):
        months = max(1, min(int(months), 36))

        periods = []

        current_month = month
        current_year = year

        for _ in range(months):
            periods.append(
                (
                    current_month,
                    current_year,
                )
            )

            (
                current_month,
                current_year,
            ) = cls._previous_month(
                current_month,
                current_year,
            )

        periods.reverse()

        return periods

    @classmethod
    def monthly_income_expense_for_period(
        cls,
        user,
        month,
        year,
        months=6,
    ):
        """
        Return historical income, expenses, and balance for a
        requested number of months ending with the selected month.
        """

        periods = cls._periods_ending_with(
            month=month,
            year=year,
            months=months,
        )

        return [
            cls._month_totals(
                user=user,
                month=period_month,
                year=period_year,
            )
            for period_month, period_year in periods
        ]

    @classmethod
    def monthly_trend(
        cls,
        user,
        months=6,
    ):
        """
        Return expense totals keyed by YYYY-MM.

        The current month is included as the final period.
        """

        today = date.today()

        records = (
            cls.monthly_income_expense_for_period(
                user=user,
                month=today.month,
                year=today.year,
                months=months,
            )
        )

        return {
            record["period"]: record["expense"]
            for record in records
        }

    @classmethod
    def monthly_income_expense(
        cls,
        user,
        months=6,
    ):
        """
        Return income, expense, and balance for each month
        ending with the current calendar month.
        """

        today = date.today()

        return cls.monthly_income_expense_for_period(
            user=user,
            month=today.month,
            year=today.year,
            months=months,
        )

    @classmethod
    def moving_average(
        cls,
        user,
        window=3,
        months=None,
    ):
        """
        Return the average monthly expense over the requested
        trailing window.
        """

        window = max(1, min(int(window), 36))

        if months is None:
            months = window

        values = list(
            cls.monthly_trend(
                user=user,
                months=months,
            ).values()
        )

        values = [
            decimal_value(value)
            for value in values[-window:]
        ]

        if not values:
            return Decimal("0.00")

        return money(
            sum(values, Decimal("0.00"))
            / Decimal(len(values))
        )

    @classmethod
    def expense_growth(
        cls,
        user,
        month=None,
        year=None,
    ):
        """
        Compare expense spending with the previous month.
        """

        today = date.today()

        month = month or today.month
        year = year or today.year

        current = cls._month_totals(
            user=user,
            month=month,
            year=year,
        )

        (
            previous_month,
            previous_year,
        ) = cls._previous_month(
            month,
            year,
        )

        previous = cls._month_totals(
            user=user,
            month=previous_month,
            year=previous_year,
        )

        current_expense = decimal_value(
            current["expense"]
        )

        previous_expense = decimal_value(
            previous["expense"]
        )

        return str(
            percentage(
                current_expense - previous_expense,
                previous_expense,
            )
        )

    @classmethod
    def income_growth(
        cls,
        user,
        month=None,
        year=None,
    ):
        """
        Compare income with the previous month.
        """

        today = date.today()

        month = month or today.month
        year = year or today.year

        current = cls._month_totals(
            user=user,
            month=month,
            year=year,
        )

        (
            previous_month,
            previous_year,
        ) = cls._previous_month(
            month,
            year,
        )

        previous = cls._month_totals(
            user=user,
            month=previous_month,
            year=previous_year,
        )

        current_income = decimal_value(
            current["income"]
        )

        previous_income = decimal_value(
            previous["income"]
        )

        return str(
            percentage(
                current_income - previous_income,
                previous_income,
            )
        )

    @classmethod
    def balance_trend(
        cls,
        user,
        months=6,
    ):
        """
        Return monthly balances keyed by YYYY-MM.
        """

        records = cls.monthly_income_expense(
            user=user,
            months=months,
        )

        return {
            record["period"]: record["balance"]
            for record in records
        }