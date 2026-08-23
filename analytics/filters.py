from django import forms
from django.db.models import Q
from django.utils import timezone

from transactions.models import Category


class AnalyticsFilterForm(forms.Form):
    """
    Filter Analytics by month, year, and category.
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

    month = forms.TypedChoiceField(
        choices=MONTH_CHOICES,
        coerce=int,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    year = forms.TypedChoiceField(
        choices=[],
        coerce=int,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

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

    def __init__(
        self,
        *args,
        user=None,
        **kwargs,
    ):
        self.user = user

        super().__init__(*args, **kwargs)

        today = timezone.localdate()

        self.fields["year"].choices = [
            (
                year,
                str(year),
            )
            for year in range(
                today.year - 4,
                today.year + 1,
            )
        ]

        if (
            user is not None
            and getattr(user, "is_authenticated", False)
        ):
            self.fields["category"].queryset = (
                Category.objects
                .filter(
                    Q(
                        user=user,
                    )
                    | Q(
                        user__isnull=True,
                        is_default=True,
                    )
                )
                .order_by("name")
            )

        initial = kwargs.get("initial") or {}

        if "month" not in initial:
            self.initial["month"] = today.month

        if "year" not in initial:
            self.initial["year"] = today.year

    def clean_month(self):
        month = self.cleaned_data.get("month")

        if month is None:
            return timezone.localdate().month

        if month < 1 or month > 12:
            raise forms.ValidationError(
                "Month must be between 1 and 12."
            )

        return month

    def clean_year(self):
        year = self.cleaned_data.get("year")

        if year is None:
            return timezone.localdate().year

        current_year = timezone.localdate().year

        if year < current_year - 4 or year > current_year:
            raise forms.ValidationError(
                "Select a valid year."
            )

        return year

    def clean(self):
        cleaned_data = super().clean()

        month = cleaned_data.get("month")
        year = cleaned_data.get("year")
        today = timezone.localdate()

        if month and year:
            if (
                year > today.year
                or (
                    year == today.year
                    and month > today.month
                )
            ):
                raise forms.ValidationError(
                    "Future months cannot be selected."
                )

        category = cleaned_data.get("category")

        if (
            category is not None
            and self.user is not None
            and category.user_id is not None
            and category.user_id != self.user.id
        ):
            self.add_error(
                "category",
                "Selected category does not belong to you.",
            )

        return cleaned_data


class DateRangeFilterForm(forms.Form):
    """
    Filter Analytics by an inclusive custom date range.
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
            cleaned_data["start_date"] = today.replace(
                day=1,
            )
            cleaned_data["end_date"] = today

            return cleaned_data

        if not start_date:
            self.add_error(
                "start_date",
                "Start date is required.",
            )

        if not end_date:
            self.add_error(
                "end_date",
                "End date is required.",
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


class ForecastFilterForm(forms.Form):
    """
    Controls the amount of history and forecast horizon.
    """

    history_months = forms.IntegerField(
        min_value=1,
        max_value=36,
        initial=12,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "max": 36,
            }
        ),
    )

    horizon = forms.IntegerField(
        min_value=1,
        max_value=12,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "max": 12,
            }
        ),
    )