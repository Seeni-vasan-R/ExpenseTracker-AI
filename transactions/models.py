from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


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
                condition=(
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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "transaction_date"]),
            models.Index(fields=["user", "category"]),
            models.Index(fields=["user", "transaction_type"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
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

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.transaction_type} - "
            f"{self.amount} on {self.transaction_date}"
        )