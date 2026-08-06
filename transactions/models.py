from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Category(models.Model):
    """
    Stores transaction categories.
    Categories can be default (global) or user-specific.
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
                check=(
                    (Q(is_default=True) & Q(user__isnull=True)) |
                    (Q(is_default=False))
                ),
                name="default_category_must_not_have_user",
            ),
        ]

    def clean(self):
        if self.is_default and self.user is not None:
            raise ValidationError(
                {"user": "Default categories must not be assigned to a user."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        owner = "Default" if self.user is None else self.user.username
        return f"{self.name} ({owner})"


def receipt_upload_path(instance, filename):
    return f'receipts/user_{instance.user.id}/{timezone.now().strftime("%Y%m")}/{filename}'


class TransactionQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

    def for_user(self, user):
        return self.filter(user=user)


class TransactionManager(models.Manager):
    def get_queryset(self):
        return TransactionQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


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
        validators=[MinValueValidator(0.01)],
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
        help_text="True if this transaction was auto-generated from a RecurringTransaction.",
    )

    recurring_source = models.ForeignKey(
        'RecurringTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_transactions',
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
            models.Index(fields=["user", "transaction_date"]),
            models.Index(fields=["user", "category"]),
            models.Index(fields=["user", "transaction_type"]),
            models.Index(fields=["user", "is_deleted"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(amount__gt=0),
                name="transaction_amount_gt_zero",
            ),
        ]

    def clean(self):
        errors = {}

        if self.category and self.category.user is not None and self.category.user != self.user:
            errors["category"] = "Selected category does not belong to this user."

        if self.transaction_type == "Income" and self.category.category_type != "Income":
            errors["transaction_type"] = (
                "Income transactions must use a category of type 'Income'."
            )

        if self.transaction_type == "Expense" and self.category.category_type == "Income":
            errors["transaction_type"] = (
                "Expense transactions cannot use a category of type 'Income'."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.transaction_type} - "
            f"{self.amount} on {self.transaction_date}"
        )


class RecurringTransaction(models.Model):
    """
    Template for generating recurring transactions automatically.
    Does not store actual transactions — Transaction rows are generated from this.
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
        validators=[MinValueValidator(0.01)],
    )

    payment_method = models.CharField(
        max_length=30,
        choices=Transaction.PAYMENT_METHODS,
    )

    description = models.TextField(blank=True)

    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
    )

    start_date = models.DateField(default=timezone.now)

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank for no end date (repeats indefinitely).",
    )

    next_occurrence = models.DateField(
        help_text="The next date a transaction should be auto-generated.",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_occurrence"]
        constraints = [
            models.CheckConstraint(
                check=Q(amount__gt=0),
                name="recurring_transaction_amount_gt_zero",
            ),
        ]

    def clean(self):
        errors = {}

        if self.category and self.category.user is not None and self.category.user != self.user:
            errors["category"] = "Selected category does not belong to this user."

        if self.transaction_type == "Income" and self.category.category_type != "Income":
            errors["transaction_type"] = (
                "Income transactions must use a category of type 'Income'."
            )

        if self.transaction_type == "Expense" and self.category.category_type == "Income":
            errors["transaction_type"] = (
                "Expense transactions cannot use a category of type 'Income'."
            )

        if self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date cannot be before start date."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.next_occurrence:
            self.next_occurrence = self.start_date
        self.full_clean()
        super().save(*args, **kwargs)

    def calculate_next_occurrence(self):
        """Returns the next date after the current next_occurrence, based on frequency."""
        from dateutil.relativedelta import relativedelta

        deltas = {
            "Daily": relativedelta(days=1),
            "Weekly": relativedelta(weeks=1),
            "Monthly": relativedelta(months=1),
            "Yearly": relativedelta(years=1),
        }
        return self.next_occurrence + deltas[self.frequency]

    def generate_transaction(self):
        """Creates a real Transaction from this recurring template for the current next_occurrence."""
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            transaction_type=self.transaction_type,
            amount=self.amount,
            payment_method=self.payment_method,
            transaction_date=self.next_occurrence,
            description=self.description,
            is_recurring_generated=True,
            recurring_source=self,
        )
        self.next_occurrence = self.calculate_next_occurrence()
        self.save(update_fields=['next_occurrence'])
        return transaction

    def __str__(self):
        return f"{self.user.username} - {self.description or self.category.name} ({self.frequency})"