from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .common import (
    decimal_value,
    get_expense_queryset,
    get_month_bounds,
    money,
)


class ForecastAnalyticsService:
    """
    Provides simple monthly expense forecasting.

    This is a baseline forecast, not a financial prediction model.
    It is intentionally dependency-free and uses least-squares
    linear regression over monthly expense totals.
    """

    @staticmethod
    def _previous_month(month, year):
        if month == 1:
            return 12, year - 1

        return month - 1, year

    @classmethod
    def _monthly_expense(
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
    def _historical_periods(
        cls,
        months,
    ):
        months = max(1, min(int(months), 36))

        today = timezone.localdate()
        month = today.month
        year = today.year

        periods = []

        for _ in range(months):
            periods.append(
                (month, year)
            )

            month, year = cls._previous_month(
                month,
                year,
            )

        periods.reverse()

        return periods

    @classmethod
    def prepare_regression_dataset(
        cls,
        user,
        months=12,
    ):
        """
        Return sequential monthly expense observations.
        """

        periods = cls._historical_periods(
            months=months,
        )

        return [
            {
                "index": index,
                "month": month,
                "year": year,
                "period": f"{year:04d}-{month:02d}",
                "expense": str(
                    cls._monthly_expense(
                        user=user,
                        month=month,
                        year=year,
                    )
                ),
            }
            for index, (month, year)
            in enumerate(periods)
        ]

    @staticmethod
    def _linear_regression(values):
        """
        Return intercept and slope for y against x,
        where x is 0, 1, 2, ...
        """

        count = len(values)

        if count == 0:
            return Decimal("0.00"), Decimal("0.00")

        if count == 1:
            return (
                decimal_value(values[0]),
                Decimal("0.00"),
            )

        x_values = [
            Decimal(index)
            for index in range(count)
        ]

        y_values = [
            decimal_value(value)
            for value in values
        ]

        x_mean = (
            sum(x_values, Decimal("0.00"))
            / Decimal(count)
        )

        y_mean = (
            sum(y_values, Decimal("0.00"))
            / Decimal(count)
        )

        numerator = sum(
            (
                (x - x_mean) * (y - y_mean)
                for x, y in zip(
                    x_values,
                    y_values,
                )
            ),
            Decimal("0.00"),
        )

        denominator = sum(
            (
                (x - x_mean) ** 2
                for x in x_values
            ),
            Decimal("0.00"),
        )

        if denominator == 0:
            slope = Decimal("0.00")
        else:
            slope = numerator / denominator

        intercept = y_mean - (
            slope * x_mean
        )

        return intercept, slope

    @classmethod
    def forecast_next_month(
        cls,
        user,
        months=12,
    ):
        """
        Forecast next month's expenses.
        """

        dataset = cls.prepare_regression_dataset(
            user=user,
            months=months,
        )

        values = [
            decimal_value(row["expense"])
            for row in dataset
        ]

        if not values:
            return {
                "forecast": "0.00",
                "confidence": "insufficient_data",
                "historical_months": 0,
                "slope": "0.00",
            }

        intercept, slope = (
            cls._linear_regression(values)
        )

        next_index = Decimal(len(values))
        forecast = intercept + (
            slope * next_index
        )

        # Expenses cannot be negative.
        forecast = max(
            Decimal("0.00"),
            forecast,
        )

        if len(values) < 3:
            confidence = "insufficient_data"
        elif len(values) < 6:
            confidence = "low"
        else:
            confidence = "baseline"

        return {
            "forecast": str(money(forecast)),
            "confidence": confidence,
            "historical_months": len(values),
            "slope": str(money(slope)),
            "last_actual": str(
                money(values[-1])
            ),
        }

    @classmethod
    def forecast_months(
        cls,
        user,
        months=12,
        horizon=3,
    ):
        """
        Forecast one or more future monthly expense values.
        """

        horizon = max(1, min(int(horizon), 12))

        dataset = cls.prepare_regression_dataset(
            user=user,
            months=months,
        )

        values = [
            decimal_value(row["expense"])
            for row in dataset
        ]

        if not values:
            return []

        intercept, slope = (
            cls._linear_regression(values)
        )

        today = timezone.localdate()
        month = today.month
        year = today.year

        results = []

        for step in range(1, horizon + 1):
            next_index = Decimal(
                len(values) + step - 1
            )

            forecast = intercept + (
                slope * next_index
            )

            forecast = max(
                Decimal("0.00"),
                forecast,
            )

            month, year = cls._next_month(
                month,
                year,
            )

            results.append(
                {
                    "month": month,
                    "year": year,
                    "period": (
                        f"{year:04d}-{month:02d}"
                    ),
                    "forecast": str(
                        money(forecast)
                    ),
                }
            )

        return results

    @classmethod
    def _next_month(cls, month, year):
        if month == 12:
            return 1, year + 1

        return month + 1, year

    @classmethod
    def get_forecast_summary(
        cls,
        user,
        months=12,
        horizon=1,
    ):
        """
        Return historical data and forecast values together.
        """

        dataset = cls.prepare_regression_dataset(
            user=user,
            months=months,
        )

        forecast = cls.forecast_next_month(
            user=user,
            months=months,
        )

        future = cls.forecast_months(
            user=user,
            months=months,
            horizon=horizon,
        )

        return {
            "historical": dataset,
            "next_month": forecast,
            "future": future,
        }