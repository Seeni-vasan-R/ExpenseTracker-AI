from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ai_summary.models import AISummary
from ai_summary.services import AISummaryService
from transactions.models import Category, Transaction


User = get_user_model()


class AISummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="summary-user",
            password="test-password",
        )

        self.income_category = (
            Category.objects.create(
                name="Salary",
                category_type="Income",
                is_default=True,
                user=None,
            )
        )

        self.expense_category = (
            Category.objects.create(
                name="Food",
                category_type="Need",
                is_default=True,
                user=None,
            )
        )

        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            transaction_type="Income",
            amount=Decimal("50000.00"),
            payment_method="Bank Transfer",
            transaction_date=date(2026, 8, 1),
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type="Expense",
            amount=Decimal("2500.00"),
            payment_method="UPI",
            transaction_date=date(2026, 8, 5),
        )

    def test_generate_returns_monthly_summary(self):
        payload = AISummaryService.generate(
            user=self.user,
            month=8,
            year=2026,
            save=True,
        )

        self.assertEqual(
            payload["month"],
            8,
        )

        self.assertEqual(
            payload["year"],
            2026,
        )

        self.assertIn(
            "summary_text",
            payload,
        )

        self.assertTrue(
            payload["insights"],
        )

        self.assertTrue(
            payload["recommendations"],
        )

        self.assertTrue(
            AISummary.objects.filter(
                user=self.user,
                month=8,
                year=2026,
            ).exists()
        )

    def test_generate_updates_existing_period(self):
        first = AISummaryService.generate(
            user=self.user,
            month=8,
            year=2026,
            save=True,
        )

        second = AISummaryService.generate(
            user=self.user,
            month=8,
            year=2026,
            save=True,
        )

        self.assertEqual(
            first["id"],
            second["id"],
        )

        self.assertEqual(
            AISummary.objects.filter(
                user=self.user,
                month=8,
                year=2026,
            ).count(),
            1,
        )

    def test_summary_page_requires_login(self):
        response = self.client.get(
            reverse("ai_summary:summary")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_summary_api_returns_json(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("ai_summary:summary-api"),
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

        self.assertEqual(
            payload["month"],
            8,
        )

        self.assertIn(
            "summary_text",
            payload,
        )

    def test_latest_api_returns_saved_summary(self):
        AISummaryService.generate(
            user=self.user,
            month=8,
            year=2026,
            save=True,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("ai_summary:latest-api")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIsNotNone(
            payload["summary"]
        )