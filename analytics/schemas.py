from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any


def _decimal_string(value):
    if value is None:
        return "0.00"

    return str(
        Decimal(str(value)).quantize(
            Decimal("0.01")
        )
    )


@dataclass
class MonthlySummarySchema:
    month: int
    year: int
    start_date: str
    end_date: str
    income: str = "0.00"
    expense: str = "0.00"
    balance: str = "0.00"
    savings_rate: str = "0.00"
    transaction_count: int = 0

    @classmethod
    def from_dict(cls, data):
        return cls(
            month=int(data.get("month", 1)),
            year=int(data.get("year", 2000)),
            start_date=data.get(
                "start_date",
                "",
            ),
            end_date=data.get(
                "end_date",
                "",
            ),
            income=_decimal_string(
                data.get("income")
            ),
            expense=_decimal_string(
                data.get("expense")
            ),
            balance=_decimal_string(
                data.get("balance")
            ),
            savings_rate=_decimal_string(
                data.get("savings_rate")
            ),
            transaction_count=int(
                data.get(
                    "transaction_count",
                    0,
                )
            ),
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class CategoryTotalSchema:
    category: str
    total: str
    category_id: int | None = None
    category_type: str | None = None
    transaction_count: int = 0

    @classmethod
    def from_dict(cls, data):
        return cls(
            category=data.get(
                "category",
                "Uncategorized",
            ),
            total=_decimal_string(
                data.get("total")
            ),
            category_id=data.get("category_id"),
            category_type=data.get(
                "category_type"
            ),
            transaction_count=int(
                data.get(
                    "transaction_count",
                    0,
                )
            ),
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class BudgetUsageSchema:
    id: int
    category: str
    budget_limit: str
    spent: str
    remaining: str
    usage_percentage: str
    is_over_budget: bool
    status: str
    start_date: str
    end_date: str
    category_id: int | None = None
    category_type: str | None = None
    transaction_count: int = 0

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=int(data["id"]),
            category=data.get(
                "category",
                "Overall",
            ),
            budget_limit=_decimal_string(
                data.get("budget_limit")
            ),
            spent=_decimal_string(
                data.get("spent")
            ),
            remaining=_decimal_string(
                data.get("remaining")
            ),
            usage_percentage=_decimal_string(
                data.get("usage_percentage")
            ),
            is_over_budget=bool(
                data.get(
                    "is_over_budget",
                    False,
                )
            ),
            status=data.get(
                "status",
                "within_budget",
            ),
            start_date=data.get(
                "start_date",
                "",
            ),
            end_date=data.get(
                "end_date",
                "",
            ),
            category_id=data.get("category_id"),
            category_type=data.get(
                "category_type"
            ),
            transaction_count=int(
                data.get(
                    "transaction_count",
                    0,
                )
            ),
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class ForecastSchema:
    forecast: str
    confidence: str
    historical_months: int
    slope: str = "0.00"
    last_actual: str = "0.00"

    @classmethod
    def from_dict(cls, data):
        return cls(
            forecast=_decimal_string(
                data.get("forecast")
            ),
            confidence=data.get(
                "confidence",
                "insufficient_data",
            ),
            historical_months=int(
                data.get(
                    "historical_months",
                    0,
                )
            ),
            slope=_decimal_string(
                data.get("slope")
            ),
            last_actual=_decimal_string(
                data.get("last_actual")
            ),
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class DashboardSchema:
    summary: dict[str, Any] = field(
        default_factory=dict
    )
    budgets: dict[str, Any] = field(
        default_factory=dict
    )
    patterns: dict[str, Any] = field(
        default_factory=dict
    )
    trend: dict[str, Any] = field(
        default_factory=dict
    )
    recent_activity: list[dict[str, Any]] = field(
        default_factory=list
    )
    category_totals: dict[str, Any] = field(
        default_factory=dict
    )
    top_categories: list[dict[str, Any]] = field(
        default_factory=list
    )
    need_want_ratio: dict[str, Any] = field(
        default_factory=dict
    )
    moving_average: str = "0.00"
    growth: dict[str, Any] = field(
        default_factory=dict
    )

    @classmethod
    def from_dict(cls, data):
        return cls(
            summary=data.get(
                "summary",
                {},
            ),
            budgets=data.get(
                "budgets",
                {},
            ),
            patterns=data.get(
                "patterns",
                {},
            ),
            trend=data.get(
                "trend",
                {},
            ),
            recent_activity=data.get(
                "recent_activity",
                [],
            ),
            category_totals=data.get(
                "category_totals",
                {},
            ),
            top_categories=data.get(
                "top_categories",
                [],
            ),
            need_want_ratio=data.get(
                "need_want_ratio",
                {},
            ),
            moving_average=_decimal_string(
                data.get("moving_average")
            ),
            growth=data.get(
                "growth",
                {},
            ),
        )

    def to_dict(self):
        return asdict(self)