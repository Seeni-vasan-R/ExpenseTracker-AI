from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Q, QuerySet
from django.utils import timezone

from transactions.models import Transaction


ZERO = Decimal("0.00")


def get_month_bounds(month, year):
    """
    Return the first and last date of a calendar month.
    """

    month = int(month)
    year = int(year)

    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    start_date = date(year, month, 1)

    end_date = date(
        year,
        month,
        monthrange(year, month)[1],
    )

    return start_date, end_date


def get_current_month_bounds():
    """
    Return the first and last date of the current month.
    """

    today = timezone.localdate()

    return get_month_bounds(
        month=today.month,
        year=today.year,
    )


def get_transaction_queryset(
    user,
    start_date=None,
    end_date=None,
    transaction_type=None,
    category=None,
):
    """
    Return active transactions belonging to one user.

    Deleted transactions are always excluded.
    """

    queryset = (
        Transaction.objects
        .active()
        .filter(user=user)
        .select_related("category")
    )

    if start_date is not None:
        queryset = queryset.filter(
            transaction_date__gte=start_date,
        )

    if end_date is not None:
        queryset = queryset.filter(
            transaction_date__lte=end_date,
        )

    if transaction_type:
        queryset = queryset.filter(
            transaction_type=transaction_type,
        )

    if category is not None:
        category_id = getattr(
            category,
            "pk",
            category,
        )

        queryset = queryset.filter(
            category_id=category_id,
        )

    return queryset


def get_month_transactions(
    user,
    month,
    year,
    transaction_type=None,
    category=None,
):
    """
    Return active transactions for one calendar month.
    """

    start_date, end_date = get_month_bounds(
        month=month,
        year=year,
    )

    return get_transaction_queryset(
        user=user,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        category=category,
    )


def get_expense_queryset(
    user,
    start_date=None,
    end_date=None,
    category=None,
):
    return get_transaction_queryset(
        user=user,
        start_date=start_date,
        end_date=end_date,
        transaction_type="Expense",
        category=category,
    )


def get_income_queryset(
    user,
    start_date=None,
    end_date=None,
):
    return get_transaction_queryset(
        user=user,
        start_date=start_date,
        end_date=end_date,
        transaction_type="Income",
    )


def decimal_value(value):
    """
    Normalize aggregate results and nullable values.
    """

    if value is None:
        return ZERO

    return Decimal(str(value))


def percentage(part, whole):
    """
    Return a percentage rounded to two decimal places.
    """

    part = decimal_value(part)
    whole = decimal_value(whole)

    if whole == 0:
        return ZERO

    return ((part / whole) * Decimal("100")).quantize(
        Decimal("0.01"),
    )


def money(value):
    """
    Return a two-decimal-place Decimal value.
    """

    return decimal_value(value).quantize(
        Decimal("0.01"),
    )


def signed_balance(income, expense):
    return money(
        decimal_value(income)
        - decimal_value(expense)
    )


def month_key(month, year):
    return f"{int(year):04d}-{int(month):02d}"


def queryset_has_rows(queryset):
    return queryset.exists()


def category_scope_filter(user):
    """
    Return a Q object matching categories visible to a user:

    - global default categories
    - categories owned by the user
    """

    return Q(
        user__isnull=True,
        is_default=True,
    ) | Q(user=user)