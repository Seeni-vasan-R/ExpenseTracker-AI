import logging
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from transactions.models import Transaction

from .services import AISummaryService


logger = logging.getLogger(__name__)


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@login_required
def summary_page(request):
    transactions = (
        Transaction.objects
        .active()
        .for_user(request.user)
    )

    total_income = (
        transactions
        .filter(
            transaction_type="Income",
        )
        .aggregate(
            total=Sum("amount"),
        )
        .get("total")
        or Decimal("0.00")
    )

    total_expense = (
        transactions
        .filter(
            transaction_type="Expense",
        )
        .aggregate(
            total=Sum("amount"),
        )
        .get("total")
        or Decimal("0.00")
    )

    balance = total_income - total_expense

    if total_income > 0:
        savings_rate = (
            balance / total_income
        ) * Decimal("100")
    else:
        savings_rate = Decimal("0.00")

    context = {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "savings_rate": savings_rate,
        "transaction_count": transactions.count(),
    }

    return render(
        request,
        "ai_summary/summary.html",
        context,
    )


@login_required
@require_GET
def summary_api(request):
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
        return JsonResponse(
            {
                "error": (
                    "Month must be between 1 and 12."
                ),
            },
            status=400,
        )

    if year < 2000:
        return JsonResponse(
            {
                "error": "Year is invalid.",
            },
            status=400,
        )

    try:
        payload = AISummaryService.generate(
            user=request.user,
            month=month,
            year=year,
            save=True,
        )

    except ValidationError as error:
        return JsonResponse(
            {
                "error": str(error),
            },
            status=400,
        )

    except Exception:
        logger.exception(
            "Unable to generate AI summary."
        )

        return JsonResponse(
            {
                "error": (
                    "The summary could not be generated. "
                    "Check the Django server terminal for details."
                ),
            },
            status=500,
        )

    return JsonResponse(payload)


@login_required
@require_GET
def latest_summary_api(request):
    summary = AISummaryService.latest(
        user=request.user,
    )

    if summary is None:
        return JsonResponse(
            {
                "summary": None,
            }
        )

    return JsonResponse(
        {
            "summary": {
                "id": summary.id,
                "month": summary.month,
                "year": summary.year,
                "summary_text": summary.summary_text,
                "insights": summary.insights,
                "recommendations": (
                    summary.recommendations
                ),
                "metrics": summary.metrics,
                "created_at": (
                    summary.created_at.isoformat()
                ),
                "updated_at": (
                    summary.updated_at.isoformat()
                ),
            }
        }
    )