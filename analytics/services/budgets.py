from decimal import Decimal

from django.db.models import Sum

from budget.models import Budget

from .common import (
    decimal_value,
    get_expense_queryset,
    get_month_bounds,
    money,
    percentage,
)


class BudgetAnalyticsService:
    """
    Calculates usage and status for monthly budgets.
    """

    @classmethod
    def get_month_budgets(
        cls,
        user,
        month,
        year,
    ):
        """
        Return active budgets for one calendar month.
        """

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        return (
            Budget.objects
            .filter(
                user=user,
                is_active=True,
                start_date=start_date,
                end_date=end_date,
            )
            .select_related("category")
            .order_by(
                "category__name",
                "created_at",
            )
        )

    @classmethod
    def _get_budget_expenses(
        cls,
        user,
        budget,
    ):
        """
        Return expenses covered by a budget.

        A category budget filters by category.
        An overall budget includes all user expenses.
        """

        queryset = get_expense_queryset(
            user=user,
            start_date=budget.start_date,
            end_date=budget.end_date,
        )

        if budget.category_id:
            queryset = queryset.filter(
                category_id=budget.category_id,
            )

        return queryset

    @classmethod
    def get_budget_usage(
        cls,
        user,
        budget,
    ):
        """
        Return usage details for one Budget instance.
        """

        expenses = cls._get_budget_expenses(
            user=user,
            budget=budget,
        )

        spent = decimal_value(
            expenses.aggregate(
                total=Sum("amount"),
            )["total"]
        )

        limit = money(budget.budget_limit)
        remaining = money(limit - spent)
        usage_percentage = percentage(
            spent,
            limit,
        )

        is_over_budget = spent > limit

        if is_over_budget:
            status = "over_budget"
        elif spent == limit:
            status = "at_limit"
        elif spent >= limit * Decimal("0.80"):
            status = "near_limit"
        else:
            status = "within_budget"

        return {
            "id": budget.id,
            "category_id": budget.category_id,
            "category": (
                budget.category.name
                if budget.category_id
                else "Overall"
            ),
            "category_type": (
                budget.category.category_type
                if budget.category_id
                else None
            ),
            "start_date": (
                budget.start_date.isoformat()
            ),
            "end_date": budget.end_date.isoformat(),
            "budget_limit": str(limit),
            "spent": str(money(spent)),
            "remaining": str(remaining),
            "usage_percentage": str(
                usage_percentage
            ),
            "is_over_budget": is_over_budget,
            "status": status,
            "transaction_count": expenses.count(),
        }

    @classmethod
    def budget_overview(
        cls,
        user,
        month,
        year,
    ):
        """
        Return all active budget usage records for a month.
        """

        budgets = cls.get_month_budgets(
            user=user,
            month=month,
            year=year,
        )

        result = [
            cls.get_budget_usage(
                user=user,
                budget=budget,
            )
            for budget in budgets
        ]

        total_limit = sum(
            (
                Decimal(item["budget_limit"])
                for item in result
            ),
            Decimal("0.00"),
        )

        total_spent = sum(
            (
                Decimal(item["spent"])
                for item in result
            ),
            Decimal("0.00"),
        )

        return {
            "month": month,
            "year": year,
            "budgets": result,
            "budget_count": len(result),
            "total_limit": str(
                money(total_limit)
            ),
            "total_spent": str(
                money(total_spent)
            ),
            "total_remaining": str(
                money(total_limit - total_spent)
            ),
            "overall_usage_percentage": str(
                percentage(
                    total_spent,
                    total_limit,
                )
            ),
        }

    @classmethod
    def over_budget(
        cls,
        user,
        month,
        year,
    ):
        """
        Return only budgets whose limits have been exceeded.
        """

        overview = cls.budget_overview(
            user=user,
            month=month,
            year=year,
        )

        return [
            budget
            for budget in overview["budgets"]
            if budget["is_over_budget"]
        ]

    @classmethod
    def budget_alerts(
        cls,
        user,
        month,
        year,
    ):
        """
        Return budgets requiring attention.
        """

        overview = cls.budget_overview(
            user=user,
            month=month,
            year=year,
        )

        return [
            budget
            for budget in overview["budgets"]
            if budget["status"]
            in {
                "over_budget",
                "at_limit",
                "near_limit",
            }
        ]

    @classmethod
    def compare_budget_to_expenses(
        cls,
        user,
        month,
        year,
    ):
        """
        Compare the total budget limits with all expenses
        in the selected month.
        """

        start_date, end_date = get_month_bounds(
            month=month,
            year=year,
        )

        overview = cls.budget_overview(
            user=user,
            month=month,
            year=year,
        )

        total_expenses = decimal_value(
            get_expense_queryset(
                user=user,
                start_date=start_date,
                end_date=end_date,
            ).aggregate(
                total=Sum("amount"),
            )["total"]
        )

        total_limit = Decimal(
            overview["total_limit"]
        )

        return {
            "total_budget_limit": str(
                money(total_limit)
            ),
            "total_budget_spent": (
                overview["total_spent"]
            ),
            "all_expenses": str(
                money(total_expenses)
            ),
            "budget_coverage_percentage": str(
                percentage(
                    total_limit,
                    total_expenses,
                )
            ),
            "expense_coverage_percentage": str(
                percentage(
                    total_expenses,
                    total_limit,
                )
            ),
        }