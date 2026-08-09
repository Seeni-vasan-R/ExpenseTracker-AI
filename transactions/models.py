from datetime import date

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction as db_transaction
from django.db.models import Q
from django.utils import timezone


def validate_positive_amount(value):
    if value <= 0:
        raise ValidationError("Amount must be greater than zero.")


class Category(models.Model):
    """
    Stores transaction categories.

    Default categories:
        - Are global.
        - Have no associated user.
        - Have is_default=True.

    Custom categories:
        - Belong to one user.
        - Have is_default=False.
    """

    CATEGORY_TYPES = [
        ("Need", "Need"),
        ("Want", "Want"),
        ("Savings", "Savings"),
        ("Income", "Income"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories",
    )

    name = models.CharField(
        max_length=100,
    )

    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPES,
    )

    is_default = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_category_name_per_user",
            ),
            models.CheckConstraint(
                condition=(
                    Q(is_default=True, user__isnull=True)
                    | Q(is_default=False)
                ),
                name="default_category_must_not_have_user",
            ),
        ]

    def clean(self):
        errors = {}

        self.name = " ".join(self.name.split())

        if not self.name:
            errors["name"] = "Category name cannot be empty."

        if self.is_default and self.user_id is not None:
            errors["user"] = "Default categories cannot belong to a user."

        if not self.is_default and self.user_id is None:
            errors["__all__"] = "Custom categories must belong to a user."

        duplicate_categories = Category.objects.filter(
            name__iexact=self.name,
            is_default=self.is_default,
        )

        if self.is_default:
            duplicate_categories = duplicate_categories.filter(
                user__isnull=True,
            )
        else:
            duplicate_categories = duplicate_categories.filter(
                user_id=self.user_id,
            )

        if self.pk:
            duplicate_categories = duplicate_categories.exclude(pk=self.pk)

        if duplicate_categories.exists():
            errors["name"] = (
                "A category with this name already exists for this owner."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.split())
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        owner = "Default" if self.user_id is None else self.user.username
        return f"{self.name} ({owner})"


def receipt_upload_path(instance, filename):
    """
    Stores receipts by user and month.

    Example:
        receipts/user_12/202608/receipt.jpg
    """
    current_month = timezone.localdate().strftime("%Y%m")
    return f"receipts/user_{instance.user_id}/{current_month}/{filename}"


class TransactionQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

    def for_user(self, user):
        return self.filter(user=user)

    def expenses(self):
        return self.filter(transaction_type="Expense")

    def income(self):
        return self.filter(transaction_type="Income")

    def between_dates(self, start_date, end_date):
        return self.filter(
            transaction_date__range=(start_date, end_date)
        )


class TransactionManager(models.Manager):
    def get_queryset(self):
        return TransactionQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def deleted(self):
        return self.get_queryset().deleted()

    def for_user(self, user):
        return self.get_queryset().for_user(user)


class Transaction(models.Model):
    """
    Stores income and expense transactions.
    """

    TRANSACTION_TYPES = [
        ("Income", "Income"),
        ("Expense", "Expense"),
    ]

    PAYMENT_METHODS = [
        ("Cash", "Cash"),
        ("UPI", "UPI"),
        ("Credit Card", "Credit Card"),
        ("Debit Card", "Debit Card"),
        ("Bank Transfer", "Bank Transfer"),
        ("Other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01),
            validate_positive_amount,
        ],
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS,
    )

    transaction_date = models.DateField()

    description = models.TextField(
        blank=True,
    )

    receipt = models.FileField(
        upload_to=receipt_upload_path,
        blank=True,
        null=True,
    )

    is_recurring_generated = models.BooleanField(
        default=False,
        help_text=(
            "True if this transaction was automatically generated "
            "from a recurring transaction."
        ),
    )

    recurring_source = models.ForeignKey(
        "RecurringTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_transactions",
    )

    is_deleted = models.BooleanField(
        default=False,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = TransactionManager()

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["user", "transaction_date"],
                name="transaction_user_date_idx",
            ),
            models.Index(
                fields=["user", "category"],
                name="transaction_user_category_idx",
            ),
            models.Index(
                fields=["user", "transaction_type"],
                name="transaction_user_type_idx",
            ),
            models.Index(
                fields=["user", "is_deleted"],
                name="transaction_user_deleted_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="transaction_amount_gt_zero",
            ),
        ]

    def clean(self):
        errors = {}

        if self.transaction_date and self.transaction_date > timezone.localdate():
            errors["transaction_date"] = (
                "Transaction date cannot be in the future."
            )

        category = None

        if self.category_id:
            try:
                category = self.category
            except Category.DoesNotExist:
                errors["category"] = "Selected category does not exist."

        if category:
            if (
                category.user_id is not None
                and category.user_id != self.user_id
            ):
                errors["category"] = (
                    "Selected category does not belong to this user."
                )

            if (
                self.transaction_type == "Income"
                and category.category_type != "Income"
            ):
                errors["transaction_type"] = (
                    "Income transactions must use an Income category."
                )

            if (
                self.transaction_type == "Expense"
                and category.category_type == "Income"
            ):
                errors["transaction_type"] = (
                    "Expense transactions cannot use an Income category."
                )

        if self.is_deleted and not self.deleted_at:
            errors["deleted_at"] = (
                "Deleted transactions must have a deletion timestamp."
            )

        if not self.is_deleted and self.deleted_at:
            errors["deleted_at"] = (
                "Active transactions cannot have a deletion timestamp."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.is_deleted and not self.deleted_at:
            self.deleted_at = timezone.now()

        if not self.is_deleted:
            self.deleted_at = None

        self.full_clean()
        return super().save(*args, **kwargs)

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save(update_fields=["is_deleted", "deleted_at"])

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.transaction_type} - "
            f"{self.amount} on {self.transaction_date}"
        )


class RecurringTransaction(models.Model):
    """
    Template used to generate actual Transaction records.
    """

    FREQUENCY_CHOICES = [
        ("Daily", "Daily"),
        ("Weekly", "Weekly"),
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_transactions",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="recurring_transactions",
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=Transaction.TRANSACTION_TYPES,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01),
            validate_positive_amount,
        ],
    )

    payment_method = models.CharField(
        max_length=30,
        choices=Transaction.PAYMENT_METHODS,
    )

    description = models.TextField(
        blank=True,
    )

    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
    )

    start_date = models.DateField(
        default=timezone.localdate,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank for no end date.",
    )

    next_occurrence = models.DateField(
        null=True,
        blank=True,
        help_text="Date on which the next transaction will be generated.",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["next_occurrence"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="recurring_transaction_amount_gt_zero",
            ),
        ]

    def clean(self):
        errors = {}

        if self.start_date is None:
            errors["start_date"] = "Start date is required."

        if self.next_occurrence is None and self.start_date:
            self.next_occurrence = self.start_date

        if (
            self.end_date
            and self.start_date
            and self.end_date < self.start_date
        ):
            errors["end_date"] = "End date cannot be before start date."

        if (
            self.next_occurrence
            and self.start_date
            and self.next_occurrence < self.start_date
        ):
            errors["next_occurrence"] = (
                "Next occurrence cannot be before the start date."
            )

        if (
            self.end_date
            and self.next_occurrence
            and self.next_occurrence > self.end_date
        ):
            errors["next_occurrence"] = (
                "Next occurrence cannot be after the end date."
            )

        category = None

        if self.category_id:
            try:
                category = self.category
            except Category.DoesNotExist:
                errors["category"] = "Selected category does not exist."

        if category:
            if (
                category.user_id is not None
                and category.user_id != self.user_id
            ):
                errors["category"] = (
                    "Selected category does not belong to this user."
                )

            if (
                self.transaction_type == "Income"
                and category.category_type != "Income"
            ):
                errors["transaction_type"] = (
                    "Income transactions must use an Income category."
                )

            if (
                self.transaction_type == "Expense"
                and category.category_type == "Income"
            ):
                errors["transaction_type"] = (
                    "Expense transactions cannot use an Income category."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.next_occurrence:
            self.next_occurrence = self.start_date

        self.full_clean()
        return super().save(*args, **kwargs)

    def calculate_next_occurrence(self):
        """
        Return the next occurrence after the current occurrence.
        """
        if not self.next_occurrence:
            raise ValidationError(
                "Cannot calculate the next occurrence without a date."
            )

        deltas = {
            "Daily": relativedelta(days=1),
            "Weekly": relativedelta(weeks=1),
            "Monthly": relativedelta(months=1),
            "Yearly": relativedelta(years=1),
        }

        try:
            delta = deltas[self.frequency]
        except KeyError:
            raise ValidationError("Invalid recurring transaction frequency.")

        return self.next_occurrence + delta

    def generate_transaction(self, as_of=None):
        """
        Generate one transaction if the recurring transaction is due.

        Uses a database lock to prevent duplicate transactions when two
        workers try to process the same recurring record simultaneously.
        """
        as_of = as_of or timezone.localdate()

        with db_transaction.atomic():
            recurring = (
                RecurringTransaction.objects
                .select_for_update()
                .select_related("user", "category")
                .get(pk=self.pk)
            )

            if not recurring.is_active:
                raise ValidationError(
                    "This recurring transaction is inactive."
                )

            if recurring.next_occurrence > as_of:
                raise ValidationError(
                    "This recurring transaction is not due yet."
                )

            if (
                recurring.end_date
                and recurring.next_occurrence > recurring.end_date
            ):
                recurring.is_active = False
                recurring.save(update_fields=["is_active"])
                raise ValidationError(
                    "This recurring transaction has expired."
                )

            generated_transaction = Transaction.objects.create(
                user=recurring.user,
                category=recurring.category,
                transaction_type=recurring.transaction_type,
                amount=recurring.amount,
                payment_method=recurring.payment_method,
                transaction_date=recurring.next_occurrence,
                description=recurring.description,
                is_recurring_generated=True,
                recurring_source=recurring,
            )

            next_occurrence = recurring.calculate_next_occurrence()

            if (
                recurring.end_date
                and next_occurrence > recurring.end_date
            ):
                recurring.is_active = False
            else:
                recurring.next_occurrence = next_occurrence

            recurring.save(
                update_fields=[
                    "next_occurrence",
                    "is_active",
                    "updated_at",
                ]
            )

            self.next_occurrence = recurring.next_occurrence
            self.is_active = recurring.is_active

            return generated_transaction

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.description or self.category.name} "
            f"({self.frequency})"
        )