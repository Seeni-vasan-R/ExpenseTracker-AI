from django.conf import settings
from django.db import models
from django.db.models import Q


class AISummary(models.Model):
    """
    Stores a generated monthly financial summary.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_summaries",
    )

    month = models.PositiveSmallIntegerField()

    year = models.PositiveIntegerField()

    summary_text = models.TextField()

    insights = models.JSONField(
        default=list,
        blank=True,
    )

    recommendations = models.JSONField(
        default=list,
        blank=True,
    )

    metrics = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-year", "-month", "-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "month",
                    "year",
                ],
                name="unique_ai_summary_user_month",
            ),
            models.CheckConstraint(
                condition=Q(
                    month__gte=1,
                    month__lte=12,
                ),
                name="ai_summary_valid_month",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "year",
                    "month",
                ],
                name="ai_summary_user_period_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.year}-{self.month:02d} AI Summary"
        )