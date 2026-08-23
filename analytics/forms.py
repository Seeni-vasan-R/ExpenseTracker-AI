from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from transactions.models import Category


class MonthYearFilterForm(forms.Form):
    """
    Filter Analytics by calendar month and year.
    """

    MONTH_CHOICES = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    year = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_year = timezone.localdate().year

        self.fields["year"].choices = [
            (year, str(year))
            for year in range(
                current_year - 4,
                current_year + 1,
            )
        ]

    def clean_month(self):
        month = self.cleaned_data.get("month")

        if not month:
            return timezone.localdate().month

        try:
            month = int(month)
        except (TypeError, ValueError):
            raise ValidationError(
                "Select a valid month."
            )

        if month < 1 or month > 12:
            raise ValidationError(
                "Month must be between 1 and 12."
            )

        return month

    def clean_year(self):
        year = self.cleaned_data.get("year")

        if not year:
            return timezone.localdate().year

        try:
            year = int(year)
        except (TypeError, ValueError):
            raise ValidationError(
                "Select a valid year."
            )

        current_year = timezone.localdate().year

        if year < current_year - 4 or year > current_year:
            raise ValidationError(
                "Select a valid year."
            )

        return year

    def clean(self):
        cleaned_data = super().clean()

        month = cleaned_data.get("month")
        year = cleaned_data.get("year")

        if month and year:
            current_date = timezone.localdate()

            if (
                year > current_date.year
                or (
                    year == current_date.year
                    and month > current_date.month
                )
            ):
                raise ValidationError(
                    "Future months cannot be selected."
                )

        return cleaned_data


class DateRangeFilterForm(forms.Form):
    """
    Filter Analytics by a custom date range.

    If no dates are supplied, the default range is
    the previous 30 days through today.
    """

    start_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": "form-control",
                "type": "date",
            },
        ),
    )

    end_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": "form-control",
                "type": "date",
            },
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        if not start_date and not end_date:
            cleaned_data["start_date"] = (
                today - timedelta(days=30)
            )
            cleaned_data["end_date"] = today
            return cleaned_data

        if start_date and not end_date:
            self.add_error(
                "end_date",
                "End date is required.",
            )

        if end_date and not start_date:
            self.add_error(
                "start_date",
                "Start date is required.",
            )

        if start_date and end_date:
            if start_date > end_date:
                self.add_error(
                    "end_date",
                    "End date must be after start date.",
                )

            if start_date > today:
                self.add_error(
                    "start_date",
                    "Start date cannot be in the future.",
                )

            if end_date > today:
                self.add_error(
                    "end_date",
                    "End date cannot be in the future.",
                )

        return cleaned_data


class AnalyticsFilterForm(MonthYearFilterForm):
    """
    Combined month/year and category Analytics filter.

    Includes both user-owned and global default categories.
    """

    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="All categories",
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user

        super().__init__(*args, **kwargs)

        if (
            user is not None
            and getattr(user, "is_authenticated", False)
        ):
            self.fields["category"].queryset = (
                Category.objects.filter(
                    Q(user=user)
                    | Q(
                        user__isnull=True,
                        is_default=True,
                    )
                )
                .order_by("name")
            )
        else:
            self.fields["category"].queryset = (
                Category.objects.none()
            )

    def clean_category(self):
        category = self.cleaned_data.get("category")

        if category is None:
            return category

        if (
            category.user_id is not None
            and category.user_id != self.user.id
        ):
            raise ValidationError(
                "Selected category does not belong to you."
            )

        return category