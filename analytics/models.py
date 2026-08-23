from django.conf import settings
from django.db import models
from django.db.models import Q


class AnalysisSnapshot(models.Model):
    """
    Stores calculated monthly analytics for a user.

    Raw transactions remain the source of truth.
    This model caches historical calculations so old
    months do not need to be recalculated repeatedly.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analysis_snapshots",
    )

    month = models.PositiveSmallIntegerField()

    year = models.PositiveIntegerField()

    income = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    expense = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    savings_rate = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0,
    )

    category_totals = models.JSONField(
        default=dict,
        blank=True,
    )

    budget_metrics = models.JSONField(
        default=dict,
        blank=True,
    )

    behaviour_metrics = models.JSONField(
        default=dict,
        blank=True,
    )

    trend_metrics = models.JSONField(
        default=dict,
        blank=True,
    )

    generated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-year", "-month"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "month", "year"],
                name="unique_analysis_snapshot_user_month",
            ),
            models.CheckConstraint(
                condition=Q(month__gte=1, month__lte=12),
                name="analysis_snapshot_valid_month",
            ),
        ]

        indexes = [
            models.Index(
                fields=["user", "year", "month"],
                name="snapshot_user_period_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.year}-{self.month:02d} Analysis"
        )