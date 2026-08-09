from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import (
    CategoryForm,
    RecurringTransactionForm,
    TransactionForm,
)
from .models import (
    Category,
    RecurringTransaction,
    Transaction,
)


User = get_user_model()


class TransactionsTestDataMixin:
    """
    Shared test data for transactions tests.
    """

    def create_user(
        self,
        username,
        email=None,
    ):
        return User.objects.create_user(
            username=username,
            email=email or f"{username}@example.com",
            password="StrongPassword123!",
        )

    def create_category(
        self,
        user,
        name="Food",
        category_type="Need",
    ):
        return Category.objects.create(
            user=user,
            name=name,
            category_type=category_type,
            is_default=False,
        )

    def create_transaction(
        self,
        user,
        category,
        transaction_type="Expense",
        amount="100.00",
        transaction_date=None,
    ):
        return Transaction.objects.create(
            user=user,
            category=category,
            transaction_type=transaction_type,
            amount=Decimal(amount),
            payment_method="Cash",
            transaction_date=transaction_date or date.today(),
            description="Test transaction",
        )


class CategoryModelTests(TransactionsTestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_user("category_user")

    def test_user_category_can_be_created(self):
        category = self.create_category(
            user=self.user,
            name="Groceries",
            category_type="Need",
        )

        self.assertEqual(category.user, self.user)
        self.assertEqual(category.name, "Groceries")
        self.assertFalse(category.is_default)

    def test_default_category_can_be_created_without_user(self):
        category = Category.objects.create(
            name="Default Food",
            category_type="Need",
            is_default=True,
        )

        self.assertIsNone(category.user)
        self.assertTrue(category.is_default)

    def test_default_category_cannot_belong_to_user(self):
        category = Category(
            user=self.user,
            name="Invalid Default",
            category_type="Need",
            is_default=True,
        )

        with self.assertRaises(ValidationError):
            category.full_clean()

    def test_custom_category_requires_user(self):
        category = Category(
            user=None,
            name="Invalid Custom",
            category_type="Need",
            is_default=False,
        )

        with self.assertRaises(ValidationError):
            category.full_clean()

    def test_category_name_is_normalized(self):
        category = Category.objects.create(
            user=self.user,
            name="  Food   and   Drinks  ",
            category_type="Want",
            is_default=False,
        )

        self.assertEqual(category.name, "Food and Drinks")

    def test_duplicate_user_category_is_rejected(self):
        self.create_category(
            user=self.user,
            name="Transport",
            category_type="Need",
        )

        duplicate = Category(
            user=self.user,
            name="transport",
            category_type="Need",
            is_default=False,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_users_can_have_categories_with_same_name(self):
        another_user = self.create_user("another_category_user")

        first_category = self.create_category(
            user=self.user,
            name="Entertainment",
            category_type="Want",
        )

        second_category = self.create_category(
            user=another_user,
            name="Entertainment",
            category_type="Want",
        )

        self.assertEqual(first_category.name, second_category.name)
        self.assertNotEqual(first_category.user, second_category.user)


class TransactionModelTests(TransactionsTestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_user("transaction_user")

        self.expense_category = self.create_category(
            user=self.user,
            name="Food",
            category_type="Need",
        )

        self.income_category = self.create_category(
            user=self.user,
            name="Salary",
            category_type="Income",
        )

    def test_expense_transaction_can_be_created(self):
        transaction = self.create_transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type="Expense",
            amount="250.00",
        )

        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.amount, Decimal("250.00"))
        self.assertEqual(transaction.transaction_type, "Expense")
        self.assertFalse(transaction.is_deleted)

    def test_income_transaction_can_be_created_with_income_category(self):
        transaction = self.create_transaction(
            user=self.user,
            category=self.income_category,
            transaction_type="Income",
            amount="50000.00",
        )

        self.assertEqual(transaction.transaction_type, "Income")
        self.assertEqual(transaction.category.category_type, "Income")

    def test_zero_amount_is_rejected(self):
        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type="Expense",
            amount=Decimal("0.00"),
            payment_method="Cash",
            transaction_date=date.today(),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_negative_amount_is_rejected(self):
        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type="Expense",
            amount=Decimal("-10.00"),
            payment_method="Cash",
            transaction_date=date.today(),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_future_transaction_date_is_rejected(self):
        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type="Expense",
            amount=Decimal("100.00"),
            payment_method="Cash",
            transaction_date=date.today() + timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_income_requires_income_category(self):
        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type="Income",
            amount=Decimal("1000.00"),
            payment_method="Bank Transfer",
            transaction_date=date.today(),
        )

        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()

        self.assertIn(
            "transaction_type",
            context.exception.message_dict,
        )

    def test_expense_cannot_use_income_category(self):
        transaction = Transaction(
            user=self.user,
            category=self.income_category,
            transaction_type="Expense",
            amount=Decimal("100.00"),
            payment_method="Cash",
            transaction_date=date.today(),
        )

        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()

        self.assertIn(
            "transaction_type",
            context.exception.message_dict,
        )

    def test_user_cannot_use_another_users_category(self):
        another_user = self.create_user("other_transaction_user")

        another_category = self.create_category(
            user=another_user,
            name="Private Category",
            category_type="Need",
        )

        transaction = Transaction(
            user=self.user,
            category=another_category,
            transaction_type="Expense",
            amount=Decimal("100.00"),
            payment_method="Cash",
            transaction_date=date.today(),
        )

        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()

        self.assertIn(
            "category",
            context.exception.message_dict,
        )

    def test_default_category_can_be_used_by_any_user(self):
        default_category = Category.objects.create(
            name="Default Utilities",
            category_type="Need",
            is_default=True,
        )

        transaction = self.create_transaction(
            user=self.user,
            category=default_category,
            transaction_type="Expense",
            amount="300.00",
        )

        self.assertEqual(transaction.category, default_category)

    def test_soft_delete_marks_transaction_deleted(self):
        transaction = self.create_transaction(
            user=self.user,
            category=self.expense_category,
        )

        transaction.soft_delete()
        transaction.refresh_from_db()

        self.assertTrue(transaction.is_deleted)
        self.assertIsNotNone(transaction.deleted_at)

        self.assertFalse(
            Transaction.objects.active().filter(
                pk=transaction.pk,
            ).exists()
        )

        self.assertTrue(
            Transaction.objects.deleted().filter(
                pk=transaction.pk,
            ).exists()
        )

    def test_restore_marks_transaction_active(self):
        transaction = self.create_transaction(
            user=self.user,
            category=self.expense_category,
        )

        transaction.soft_delete()
        transaction.restore()
        transaction.refresh_from_db()

        self.assertFalse(transaction.is_deleted)
        self.assertIsNone(transaction.deleted_at)

        self.assertTrue(
            Transaction.objects.active().filter(
                pk=transaction.pk,
            ).exists()
        )

    def test_active_queryset_returns_only_active_transactions(self):
        active_transaction = self.create_transaction(
            user=self.user,
            category=self.expense_category,
            amount="100.00",
        )

        deleted_transaction = self.create_transaction(
            user=self.user,
            category=self.expense_category,
            amount="200.00",
        )

        deleted_transaction.soft_delete()

        active_transactions = Transaction.objects.active()

        self.assertIn(active_transaction, active_transactions)
        self.assertNotIn(deleted_transaction, active_transactions)

    def test_for_user_queryset_isolated(self):
        another_user = self.create_user("isolated_user")

        another_category = self.create_category(
            user=another_user,
            name="Other Food",
            category_type="Need",
        )

        user_transaction = self.create_transaction(
            user=self.user,
            category=self.expense_category,
        )

        another_transaction = self.create_transaction(
            user=another_user,
            category=another_category,
        )

        user_transactions = Transaction.objects.for_user(self.user)

        self.assertIn(user_transaction, user_transactions)
        self.assertNotIn(another_transaction, user_transactions)


class CategoryFormTests(TransactionsTestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_user("category_form_user")

    def test_category_form_creates_user_category(self):
        form = CategoryForm(
            data={
                "name": "Travel",
                "category_type": "Want",
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

        category = form.save()

        self.assertEqual(category.user, self.user)
        self.assertFalse(category.is_default)

    def test_category_form_rejects_duplicate_name(self):
        self.create_category(
            user=self.user,
            name="Shopping",
            category_type="Want",
        )

        form = CategoryForm(
            data={
                "name": "shopping",
                "category_type": "Want",
            },
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_category_form_requires_user(self):
        form = CategoryForm(
            data={
                "name": "Travel",
                "category_type": "Want",
            },
            user=None,
        )

        self.assertFalse(form.is_valid())
        self.assertTrue(
            form.non_field_errors()
            or form.errors
        )


class TransactionFormTests(TransactionsTestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_user("transaction_form_user")

        self.category = self.create_category(
            user=self.user,
            name="Food",
            category_type="Need",
        )

        self.income_category = self.create_category(
            user=self.user,
            name="Salary",
            category_type="Income",
        )

    def get_valid_data(self):
        return {
            "transaction_type": "Expense",
            "category": self.category.pk,
            "amount": "125.50",
            "payment_method": "UPI",
            "transaction_date": date.today().strftime("%Y-%m-%d"),
            "description": "Lunch",
        }

    def test_transaction_form_is_valid(self):
        form = TransactionForm(
            data=self.get_valid_data(),
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_transaction_form_assigns_user(self):
        form = TransactionForm(
            data=self.get_valid_data(),
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

        transaction = form.save()

        self.assertEqual(transaction.user, self.user)

    def test_transaction_form_rejects_future_date(self):
        data = self.get_valid_data()
        data["transaction_date"] = (
            date.today() + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        form = TransactionForm(
            data=data,
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("transaction_date", form.errors)

    def test_transaction_form_rejects_income_with_expense_category(self):
        data = self.get_valid_data()
        data["transaction_type"] = "Income"

        form = TransactionForm(
            data=data,
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "category",
            form.errors,
        )

    def test_transaction_form_rejects_expense_with_income_category(self):
        data = self.get_valid_data()
        data["category"] = self.income_category.pk

        form = TransactionForm(
            data=data,
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "category",
            form.errors,
        )

    def test_transaction_form_requires_authenticated_user(self):
        form = TransactionForm(
            data=self.get_valid_data(),
            user=None,
        )

        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class RecurringTransactionTests(TransactionsTestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_user("recurring_user")

        self.category = self.create_category(
            user=self.user,
            name="Subscriptions",
            category_type="Need",
        )

    def create_recurring_transaction(self):
        yesterday = date.today() - timedelta(days=1)

        return RecurringTransaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type="Expense",
            amount=Decimal("99.99"),
            payment_method="UPI",
            description="Monthly subscription",
            frequency="Daily",
            start_date=yesterday,
            end_date=date.today() + timedelta(days=5),
            next_occurrence=yesterday,
            is_active=True,
        )

    def test_recurring_transaction_can_be_created(self):
        recurring = self.create_recurring_transaction()

        self.assertEqual(recurring.user, self.user)
        self.assertEqual(recurring.frequency, "Daily")
        self.assertTrue(recurring.is_active)

    def test_next_occurrence_is_calculated(self):
        recurring = self.create_recurring_transaction()

        expected_date = recurring.next_occurrence + timedelta(days=1)

        self.assertEqual(
            recurring.calculate_next_occurrence(),
            expected_date,
        )

    def test_recurring_transaction_generates_transaction(self):
        recurring = self.create_recurring_transaction()

        generated = recurring.generate_transaction(
            as_of=date.today(),
        )

        self.assertIsInstance(generated, Transaction)
        self.assertEqual(generated.user, self.user)
        self.assertEqual(generated.category, self.category)
        self.assertTrue(generated.is_recurring_generated)
        self.assertEqual(generated.recurring_source, recurring)

        self.assertEqual(
            Transaction.objects.filter(
                recurring_source=recurring,
            ).count(),
            1,
        )

    def test_recurring_transaction_does_not_generate_before_due_date(self):
        recurring = RecurringTransaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type="Expense",
            amount=Decimal("99.99"),
            payment_method="UPI",
            description="Future subscription",
            frequency="Daily",
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            next_occurrence=date.today() + timedelta(days=1),
            is_active=True,
        )

        with self.assertRaises(ValidationError):
            recurring.generate_transaction(
                as_of=date.today(),
            )

        self.assertEqual(
            Transaction.objects.filter(
                recurring_source=recurring,
            ).count(),
            0,
        )

    def test_recurring_transaction_becomes_inactive_after_end_date(self):
        recurring = RecurringTransaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type="Expense",
            amount=Decimal("99.99"),
            payment_method="UPI",
            description="Final subscription",
            frequency="Daily",
            start_date=date.today() - timedelta(days=1),
            end_date=date.today(),
            next_occurrence=date.today(),
            is_active=True,
        )

        recurring.generate_transaction(as_of=date.today())
        recurring.refresh_from_db()

        self.assertFalse(recurring.is_active)

    def test_recurring_transaction_form_is_valid(self):
        form = RecurringTransactionForm(
            data={
                "transaction_type": "Expense",
                "category": self.category.pk,
                "amount": "250.00",
                "payment_method": "Bank Transfer",
                "description": "Rent",
                "frequency": "Monthly",
                "start_date": date.today().strftime("%Y-%m-%d"),
                "end_date": "",
                "is_active": "on",
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_recurring_form_rejects_end_date_before_start_date(self):
        form = RecurringTransactionForm(
            data={
                "transaction_type": "Expense",
                "category": self.category.pk,
                "amount": "250.00",
                "payment_method": "Bank Transfer",
                "description": "Rent",
                "frequency": "Monthly",
                "start_date": date.today().strftime("%Y-%m-%d"),
                "end_date": (
                    date.today() - timedelta(days=1)
                ).strftime("%Y-%m-%d"),
                "is_active": "on",
            },
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("end_date", form.errors)