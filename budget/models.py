from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class Budget(models.Model):
    """
    Stores overall or category-based budgets.

    If category is NULL:
        The budget applies to all expenses for the user.

    If category is set:
        The budget applies only to that category.
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
            MinValueValidator(0.01),
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
                fields=["user", "is_active"],
                name="budget_user_active_idx",
            ),
            models.Index(
                fields=["user", "start_date", "end_date"],
                name="budget_user_dates_idx",
            ),
            models.Index(
                fields=["user", "category", "is_active"],
                name="budget_user_category_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(budget_limit__gt=0),
                name="budget_limit_gt_zero",
            ),
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="budget_end_date_gte_start_date",
            ),
        ]

    def clean(self):
        errors = {}

        if self.user_id is None:
            errors["__all__"] = "A budget must belong to a user."

        if self.budget_limit is not None and self.budget_limit <= 0:
            errors["budget_limit"] = (
                "Budget limit must be greater than zero."
            )

        if self.start_date is None:
            errors["start_date"] = "Start date is required."

        if self.end_date is None:
            errors["end_date"] = "End date is required."

        if (
            self.start_date
            and self.end_date
            and self.end_date < self.start_date
        ):
            errors["end_date"] = (
                "End date cannot be before the start date."
            )

        category = None

        if self.category_id:
            try:
                category = self.category
            except self.category.RelatedObjectDoesNotExist:
                errors["category"] = (
                    "The selected category does not exist."
                )

        if category:
            if (
                category.user_id is not None
                and category.user_id != self.user_id
            ):
                errors["category"] = (
                    "Selected category does not belong to this user."
                )

            if category.category_type == "Income":
                errors["category"] = (
                    "Income categories cannot be used for budgets."
                )

        if (
            self.user_id
            and self.start_date
            and self.end_date
        ):
            overlapping_budgets = (
                Budget.objects.filter(
                    user_id=self.user_id,
                    category_id=self.category_id,
                    is_active=True,
                    start_date__lte=self.end_date,
                    end_date__gte=self.start_date,
                )
                .exclude(pk=self.pk)
            )

            if overlapping_budgets.exists():
                if self.category_id:
                    errors["category"] = (
                        "An active budget for this category already "
                        "exists during the selected date range."
                    )
                else:
                    errors["__all__"] = (
                        "An active overall budget already exists "
                        "during the selected date range."
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        if self.category_id:
            return (
                f"{self.user.username} - "
                f"{self.category.name} Budget"
            )

        return f"{self.user.username} - Overall Budget"