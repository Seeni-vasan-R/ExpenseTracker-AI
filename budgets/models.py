from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class Budget(models.Model):
    """
    Stores overall or category-based budgets.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets",
    )

    category = models.ForeignKey(
        "transactions.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="budgets",
    )

    budget_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01)
        ],
    )

    start_date = models.DateField()

    end_date = models.DateField()

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
        ordering = ["-start_date"]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "is_active",
                ]
            ),
            models.Index(
                fields=[
                    "user",
                    "start_date",
                    "end_date",
                ]
            ),
        ]

        constraints = [
            models.CheckConstraint(
                check=Q(
                    budget_limit__gt=0
                ),
                name="budget_limit_gt_zero",
            ),

            models.CheckConstraint(
                check=Q(
                    end_date__gte=F("start_date")
                ),
                name="budget_end_date_gte_start_date",
            ),
        ]

    def clean(self):
        """
        Model-level validation.
        """

        errors = {}

        # Category Ownership Validation
        if (
            self.category
            and self.category.user is not None
            and self.category.user != self.user
        ):
            errors["category"] = (
                "Selected category does not belong to this user."
            )

        # Prevent Income Categories
        if (
            self.category
            and self.category.category_type == "Income"
        ):
            errors["category"] = (
                "Income categories cannot be used for budgets."
            )

        # Prevent Overlapping Active Budgets
        overlapping_budgets = (
            Budget.objects.filter(
                user=self.user,
                category=self.category,
                is_active=True,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            ).exclude(pk=self.pk)
        )

        if overlapping_budgets.exists():

            if self.category:
                errors["category"] = (
                    "An active budget for this category "
                    "already exists in the selected date range."
                )
            else:
                errors["category"] = (
                    "An active overall budget already exists "
                    "in the selected date range."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.category:
            return (
                f"{self.user.username} - "
                f"{self.category.name} Budget"
            )

        return (
            f"{self.user.username} - Overall Budget"
        )