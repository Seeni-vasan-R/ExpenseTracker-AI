from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from analytics.models import AnalysisSnapshot
from analytics.services.budgets import (
    BudgetAnalyticsService,
)
from analytics.services.categories import (
    CategoryAnalyticsService,
)
from analytics.services.dashboard import (
    DashboardAnalyticsService,
)
from analytics.services.forecast import (
    ForecastAnalyticsService,
)
from analytics.services.trends import (
    TrendAnalyticsService,
)
from budget.models import Budget
from transactions.models import Category, Transaction


User = get_user_model()


class AnalyticsTestMixin:
    def create_user(self, username="analytics-user"):
        return User.objects.create_user(
            username=username,
            password="test-password",
        )

    def create_default_category(
        self,
        name="Food",
        category_type="Need",
    ):
        return Category.objects.create(
            name=name,
            category_type=category_type,
            is_default=True,
            user=None,
        )

    def create_user_category(
        self,
        user,
        name="Personal",
        category_type="Want",
    ):
        return Category.objects.create(
            name=name,
            category_type=category_type,
            is_default=False,
            user=user,
        )

    def create_transaction(
        self,
        user,
        category,
        amount,
        transaction_type="Expense",
        transaction_date=date(2026, 8, 10),
        is_deleted=False,
    ):
        return Transaction.objects.create(
            user=user,
            category=category,
            transaction_type=transaction_type,
            amount=Decimal(str(amount)),
            payment_method="Cash",
            transaction_date=transaction_date,
            description="Analytics test transaction",
            is_deleted=is_deleted,
        )


class AnalyticsServiceTests(
    AnalyticsTestMixin,
    TestCase,
):
    def setUp(self):
        self.user = self.create_user()

        self.food_category = (
            self.create_default_category()
        )

        self.income_category = (
            self.create_default_category(
                name="Salary",
                category_type="Income",
            )
        )

        self.want_category = (
            self.create_user_category(
                user=self.user,
                name="Shopping",
                category_type="Want",
            )
        )

        self.create_transaction(
            user=self.user,
            category=self.income_category,
            amount="50000.00",
            transaction_type="Income",
            transaction_date=date(2026, 8, 1),
        )

        self.create_transaction(
            user=self.user,
            category=self.food_category,
            amount="1000.00",
            transaction_date=date(2026, 8, 5),
        )

        self.create_transaction(
            user=self.user,
            category=self.want_category,
            amount="2000.00",
            transaction_date=date(2026, 8, 6),
        )

    def test_dashboard_summary_excludes_deleted_transactions(self):
        deleted_transaction = (
            self.create_transaction(
                user=self.user,
                category=self.food_category,
                amount="9000.00",
                transaction_date=date(2026, 8, 7),
                is_deleted=True,
            )
        )

        summary = (
            DashboardAnalyticsService
            .get_dashboard_summary(
                user=self.user,
                month=8,
                year=2026,
            )
        )

        self.assertEqual(
            summary["income"],
            "50000.00",
        )

        self.assertEqual(
            summary["expense"],
            "3000.00",
        )

        self.assertEqual(
            summary["balance"],
            "47000.00",
        )

        self.assertEqual(
            summary["transaction_count"],
            3,
        )

        self.assertTrue(
            deleted_transaction.is_deleted
        )

    def test_category_totals_group_expenses(self):
        totals = (
            CategoryAnalyticsService
            .category_totals(
                user=self.user,
                month=8,
                year=2026,
            )
        )

        self.assertEqual(
            totals["Food"],
            Decimal("1000.00"),
        )

        self.assertEqual(
            totals["Shopping"],
            Decimal("2000.00"),
        )

    def test_need_want_ratio(self):
        result = (
            CategoryAnalyticsService
            .need_want_ratio(
                user=self.user,
                month=8,
                year=2026,
            )
        )

        self.assertEqual(
            result["need"],
            "1000.00",
        )

        self.assertEqual(
            result["want"],
            "2000.00",
        )

        self.assertEqual(
            result["total_expense"],
            "3000.00",
        )

        self.assertEqual(
            result["need_percentage"],
            "33.33",
        )

        self.assertEqual(
            result["want_percentage"],
            "66.67",
        )

    def test_overall_budget_includes_all_expenses(self):
        budget = Budget.objects.create(
            user=self.user,
            category=None,
            budget_limit=Decimal("5000.00"),
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            is_active=True,
        )

        result = (
            BudgetAnalyticsService
            .get_budget_usage(
                user=self.user,
                budget=budget,
            )
        )

        self.assertEqual(
            result["spent"],
            "3000.00",
        )

        self.assertEqual(
            result["remaining"],
            "2000.00",
        )

        self.assertEqual(
            result["usage_percentage"],
            "60.00",
        )

        self.assertFalse(
            result["is_over_budget"]
        )

    def test_category_budget_only_includes_selected_category(
        self,
    ):
        budget = Budget.objects.create(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("1500.00"),
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            is_active=True,
        )

        result = (
            BudgetAnalyticsService
            .get_budget_usage(
                user=self.user,
                budget=budget,
            )
        )

        self.assertEqual(
            result["spent"],
            "1000.00",
        )

        self.assertEqual(
            result["remaining"],
            "500.00",
        )

    def test_monthly_trend_returns_selected_months(self):
        trend = (
            TrendAnalyticsService
            .monthly_income_expense(
                user=self.user,
                months=2,
            )
        )

        self.assertEqual(len(trend), 2)

        self.assertEqual(
            trend[-1]["period"],
            "2026-08",
        )

        self.assertEqual(
            trend[-1]["expense"],
            Decimal("3000.00"),
        )

    def test_forecast_dataset_contains_expense_values(self):
        dataset = (
            ForecastAnalyticsService
            .prepare_regression_dataset(
                user=self.user,
                months=3,
            )
        )

        self.assertEqual(len(dataset), 3)

        self.assertEqual(
            dataset[-1]["period"],
            "2026-08",
        )

        self.assertEqual(
            dataset[-1]["expense"],
            "3000.00",
        )

    def test_snapshot_unique_period_per_user(self):
        AnalysisSnapshot.objects.create(
            user=self.user,
            month=8,
            year=2026,
            income=Decimal("50000.00"),
            expense=Decimal("3000.00"),
            balance=Decimal("47000.00"),
        )

        with self.assertRaises(Exception):
            AnalysisSnapshot.objects.create(
                user=self.user,
                month=8,
                year=2026,
                income=Decimal("50000.00"),
                expense=Decimal("3000.00"),
                balance=Decimal("47000.00"),
            )


class AnalyticsViewTests(
    AnalyticsTestMixin,
    TestCase,
):
    def setUp(self):
        self.user = self.create_user(
            username="view-user",
        )

        self.category = (
            self.create_default_category()
        )

        self.create_transaction(
            user=self.user,
            category=self.category,
            amount="750.00",
            transaction_date=date(2026, 8, 10),
        )

        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(
            reverse("analytics:dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_dashboard_returns_json_for_authenticated_user(
        self,
    ):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("analytics:dashboard"),
            {
                "month": 8,
                "year": 2026,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/json",
        )

        payload = response.json()

        self.assertIn(
            "summary",
            payload,
        )

        self.assertEqual(
            payload["summary"]["expense"],
            "750.00",
        )

    def test_monthly_chart_returns_chart_payload(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("analytics:monthly-chart"),
            {
                "months": 3,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIn(
            "labels",
            payload,
        )

        self.assertIn(
            "values",
            payload,
        )

        self.assertEqual(
            len(payload["labels"]),
            3,
        )

        self.assertEqual(
            len(payload["values"]),
            3,
        )

    def test_category_chart_returns_chart_payload(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("analytics:category-chart"),
            {
                "month": 8,
                "year": 2026,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIn(
            "labels",
            payload,
        )

        self.assertIn(
            "values",
            payload,
        )

        self.assertIn(
            "Food",
            payload["labels"],
        )

    def test_recent_transactions_excludes_deleted_rows(self):
        self.create_transaction(
            user=self.user,
            category=self.category,
            amount="9999.00",
            transaction_date=date(2026, 8, 11),
            is_deleted=True,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("analytics:recent-transactions"),
            {
                "limit": 20,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        amounts = [
            item["amount"]
            for item in payload["transactions"]
        ]

        self.assertIn(
            "750.00",
            amounts,
        )

        self.assertNotIn(
            "9999.00",
            amounts,
        )