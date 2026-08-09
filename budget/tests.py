from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from transactions.models import Category

from .forms import BudgetForm
from .models import Budget


User = get_user_model()


class BudgetModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="budget_user",
            email="budget@example.com",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="StrongPassword123!",
        )

        self.food_category = Category.objects.create(
            user=self.user,
            name="Food",
            category_type="Need",
            is_default=False,
        )

        self.other_category = Category.objects.create(
            user=self.other_user,
            name="Other Food",
            category_type="Need",
            is_default=False,
        )

        self.income_category = Category.objects.create(
            user=self.user,
            name="Salary",
            category_type="Income",
            is_default=False,
        )

        self.default_category = Category.objects.create(
            name="Transport",
            category_type="Want",
            is_default=True,
            user=None,
        )

        self.start_date = date(2026, 8, 1)
        self.end_date = date(2026, 8, 31)

    def create_budget(self, **kwargs):
        defaults = {
            "user": self.user,
            "category": self.food_category,
            "budget_limit": Decimal("5000.00"),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": True,
        }

        defaults.update(kwargs)
        return Budget.objects.create(**defaults)

    def test_category_budget_can_be_created(self):
        budget = self.create_budget()

        self.assertEqual(budget.user, self.user)
        self.assertEqual(budget.category, self.food_category)
        self.assertEqual(
            budget.budget_limit,
            Decimal("5000.00"),
        )
        self.assertTrue(budget.is_active)

    def test_overall_budget_can_be_created(self):
        budget = self.create_budget(category=None)

        self.assertIsNone(budget.category)
        self.assertEqual(budget.user, self.user)

    def test_default_category_can_be_used(self):
        budget = self.create_budget(
            category=self.default_category,
        )

        self.assertEqual(
            budget.category,
            self.default_category,
        )

    def test_budget_str_for_category_budget(self):
        budget = self.create_budget()

        self.assertEqual(
            str(budget),
            "budget_user - Food Budget",
        )

    def test_budget_str_for_overall_budget(self):
        budget = self.create_budget(category=None)

        self.assertEqual(
            str(budget),
            "budget_user - Overall Budget",
        )

    def test_negative_budget_limit_is_rejected(self):
        budget = Budget(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("-100.00"),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        with self.assertRaises(ValidationError):
            budget.full_clean()

    def test_zero_budget_limit_is_rejected(self):
        budget = Budget(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("0.00"),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        with self.assertRaises(ValidationError):
            budget.full_clean()

    def test_end_date_before_start_date_is_rejected(self):
        budget = Budget(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("5000.00"),
            start_date=date(2026, 8, 31),
            end_date=date(2026, 8, 1),
        )

        with self.assertRaises(ValidationError):
            budget.full_clean()

    def test_other_users_category_is_rejected(self):
        budget = Budget(
            user=self.user,
            category=self.other_category,
            budget_limit=Decimal("5000.00"),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        with self.assertRaises(ValidationError):
            budget.full_clean()

    def test_income_category_is_rejected(self):
        budget = Budget(
            user=self.user,
            category=self.income_category,
            budget_limit=Decimal("5000.00"),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        with self.assertRaises(ValidationError):
            budget.full_clean()

    def test_overlapping_active_category_budget_is_rejected(self):
        self.create_budget()

        overlapping_budget = Budget(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("3000.00"),
            start_date=date(2026, 8, 15),
            end_date=date(2026, 9, 15),
            is_active=True,
        )

        with self.assertRaises(ValidationError):
            overlapping_budget.full_clean()

    def test_non_overlapping_category_budget_is_allowed(self):
        self.create_budget()

        non_overlapping_budget = Budget(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("3000.00"),
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            is_active=True,
        )

        non_overlapping_budget.full_clean()

    def test_inactive_overlapping_budget_is_allowed(self):
        self.create_budget()

        inactive_budget = Budget(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("3000.00"),
            start_date=date(2026, 8, 15),
            end_date=date(2026, 9, 15),
            is_active=False,
        )

        inactive_budget.full_clean()

    def test_overlapping_overall_budget_is_rejected(self):
        self.create_budget(category=None)

        overlapping_budget = Budget(
            user=self.user,
            category=None,
            budget_limit=Decimal("3000.00"),
            start_date=date(2026, 8, 15),
            end_date=date(2026, 9, 15),
            is_active=True,
        )

        with self.assertRaises(ValidationError):
            overlapping_budget.full_clean()

    def test_different_users_can_have_same_category_budget_period(self):
        Budget.objects.create(
            user=self.user,
            category=self.food_category,
            budget_limit=Decimal("5000.00"),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
        )

        other_user_budget = Budget(
            user=self.other_user,
            category=self.other_category,
            budget_limit=Decimal("5000.00"),
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
        )

        other_user_budget.full_clean()


class BudgetFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="form_user",
            email="form@example.com",
            password="StrongPassword123!",
        )

        self.category = Category.objects.create(
            user=self.user,
            name="Groceries",
            category_type="Need",
            is_default=False,
        )

        self.income_category = Category.objects.create(
            user=self.user,
            name="Income",
            category_type="Income",
            is_default=False,
        )

    def valid_form_data(self, **kwargs):
        data = {
            "category": str(self.category.pk),
            "budget_limit": "2500.00",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "is_active": True,
        }

        data.update(kwargs)
        return data

    def test_valid_budget_form(self):
        form = BudgetForm(
            data=self.valid_form_data(),
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_overall_budget_form_is_valid(self):
        form = BudgetForm(
            data=self.valid_form_data(category=""),
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_income_category_is_not_available(self):
        form = BudgetForm(
            data=self.valid_form_data(
                category=str(self.income_category.pk),
            ),
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)

    def test_invalid_date_range_is_rejected(self):
        form = BudgetForm(
            data=self.valid_form_data(
                start_date="2026-08-31",
                end_date="2026-08-01",
            ),
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("end_date", form.errors)

    def test_zero_budget_limit_is_rejected(self):
        form = BudgetForm(
            data=self.valid_form_data(
                budget_limit="0.00",
            ),
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("budget_limit", form.errors)

    def test_form_requires_authenticated_user(self):
        form = BudgetForm(
            data=self.valid_form_data(),
            user=None,
        )

        self.assertFalse(form.is_valid())

    def test_form_save_assigns_user(self):
        form = BudgetForm(
            data=self.valid_form_data(),
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

        budget = form.save()

        self.assertEqual(budget.user, self.user)
        self.assertEqual(budget.category, self.category)