from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .services import (
    CategoryAnalyticsService,
    DashboardAnalyticsService,
    ForecastAnalyticsService,
    TransactionAnalyticsService,
    TrendAnalyticsService,
)


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_month_year(request):
    today = timezone.localdate()

    month = _safe_int(
        request.GET.get("month"),
        today.month,
    )

    year = _safe_int(
        request.GET.get("year"),
        today.year,
    )

    if month < 1 or month > 12:
        month = today.month

    if year < 2000 or year > today.year:
        year = today.year

    if (
        year == today.year
        and month > today.month
    ):
        month = today.month

    return month, year


def _json_error(message, status=400):
    return JsonResponse(
        {
            "error": message,
        },
        status=status,
    )


@login_required
def dashboard_page(request):
    return render(
        request,
        "analytics/dashboard.html",
    )


@login_required
@require_GET
def dashboard_api(request):
    try:
        month, year = _get_month_year(request)

        summary = (
            DashboardAnalyticsService
            .get_dashboard_summary(
                user=request.user,
                month=month,
                year=year,
            )
        )

        return JsonResponse(
            {
                "summary": summary,
            }
        )

    except ValidationError as error:
        return _json_error(
            str(error),
            status=400,
        )

    except Exception:
        return _json_error(
            "Unable to load monthly Analytics data.",
            status=500,
        )


@login_required
@require_GET
def category_chart(request):
    try:
        month, year = _get_month_year(request)

        totals = (
            CategoryAnalyticsService
            .category_totals(
                user=request.user,
                month=month,
                year=year,
            )
        )

        return JsonResponse(
            {
                "labels": list(totals.keys()),
                "values": [
                    float(value)
                    for value in totals.values()
                ],
            }
        )

    except Exception:
        return _json_error(
            "Unable to load category chart data.",
            status=500,
        )


@login_required
@require_GET
def timeline_chart(request):
    try:
        month, year = _get_month_year(request)

        timeline = (
            TransactionAnalyticsService
            .daily_income_expense_timeline(
                user=request.user,
                month=month,
                year=year,
            )
        )

        return JsonResponse(timeline)

    except Exception:
        return _json_error(
            "Unable to load daily timeline data.",
            status=500,
        )


@login_required
@require_GET
def month_view_chart(request):
    try:
        month, year = _get_month_year(request)

        months = _safe_int(
            request.GET.get("months"),
            6,
        )

        months = max(2, min(months, 24))

        records = (
            TrendAnalyticsService
            .monthly_income_expense_for_period(
                user=request.user,
                month=month,
                year=year,
                months=months,
            )
        )

        return JsonResponse(
            {
                "labels": [
                    record["period"]
                    for record in records
                ],
                "income": [
                    float(
                        Decimal(record["income"])
                    )
                    for record in records
                ],
                "expense": [
                    float(
                        Decimal(record["expense"])
                    )
                    for record in records
                ],
                "balance": [
                    float(
                        Decimal(record["balance"])
                    )
                    for record in records
                ],
            }
        )

    except Exception:
        return _json_error(
            "Unable to load month-view chart data.",
            status=500,
        )


@login_required
@require_GET
def expense_calendar_chart(request):
    try:
        month, year = _get_month_year(request)

        calendar = (
            TransactionAnalyticsService
            .monthly_expense_calendar(
                user=request.user,
                month=month,
                year=year,
            )
        )

        return JsonResponse(calendar)

    except Exception:
        return _json_error(
            "Unable to load spending calendar data.",
            status=500,
        )


@login_required
@require_GET
def forecast_features(request):
    months = _safe_int(
        request.GET.get("months"),
        12,
    )

    months = max(1, min(months, 36))

    try:
        dataset = (
            ForecastAnalyticsService
            .prepare_regression_dataset(
                user=request.user,
                months=months,
            )
        )

        return JsonResponse(
            {
                "months": months,
                "dataset": dataset,
            }
        )

    except Exception:
        return _json_error(
            "Unable to load forecast data.",
            status=500,
        )