from decimal import Decimal

from django import template


register = template.Library()


CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}


@register.simple_tag(takes_context=True)
def currency_symbol(context):
    request = context.get("request")

    if request is None:
        return "₹"

    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return "₹"

    profile = getattr(user, "profile", None)

    if profile is None:
        return "₹"

    return CURRENCY_SYMBOLS.get(
        profile.currency,
        "₹",
    )


@register.filter
def currency_value(value):
    if value is None:
        return "0.00"

    try:
        return f"{Decimal(value):,.2f}"
    except (
        TypeError,
        ValueError,
        ArithmeticError,
    ):
        return value