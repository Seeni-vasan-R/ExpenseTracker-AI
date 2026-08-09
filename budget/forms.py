from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from transactions.models import Category

from .models import Budget


class BudgetForm(forms.ModelForm):
    """
    Form for creating and editing user-owned budgets.
    """

    class Meta:
        model = Budget
        fields = [
            "category",
            "budget_limit",
            "start_date",
            "end_date",
            "is_active",
        ]

        widgets = {
            "category": forms.Select(),
            "budget_limit": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Enter budget limit",
                }
            ),
            "start_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
            "end_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user

        super().__init__(*args, **kwargs)

        self._apply_bootstrap_classes()
        self._configure_category_field()
        self._assign_user_to_new_instance()

    def _apply_bootstrap_classes(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

    def _configure_category_field(self):
        category_field = self.fields["category"]

        category_field.required = False
        category_field.empty_label = "Overall budget"

        if (
            self.user is not None
            and getattr(self.user, "is_authenticated", False)
        ):
            category_field.queryset = (
                Category.objects.filter(
                    Q(user=self.user)
                    | Q(user__isnull=True, is_default=True)
                )
                .exclude(category_type="Income")
                .order_by("name")
            )
        else:
            category_field.queryset = Category.objects.none()

    def _assign_user_to_new_instance(self):
        if (
            self.user is not None
            and getattr(self.user, "is_authenticated", False)
            and not self.instance.pk
        ):
            self.instance.user = self.user

    def clean(self):
        cleaned_data = super().clean()

        if (
            self.user is None
            or not getattr(self.user, "is_authenticated", False)
        ):
            raise ValidationError(
                "An authenticated user is required."
            )

        if (
            self.instance.pk
            and self.instance.user_id != self.user.id
        ):
            raise ValidationError(
                "You are not allowed to modify this budget."
            )

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        category = cleaned_data.get("category")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "End date cannot be before the start date.",
            )

        if category:
            if (
                category.user_id is not None
                and category.user_id != self.user.id
            ):
                self.add_error(
                    "category",
                    "Selected category does not belong to you.",
                )

            if category.category_type == "Income":
                self.add_error(
                    "category",
                    "Income categories cannot be used for budgets.",
                )

        return cleaned_data

    def save(self, commit=True):
        if (
            self.user is None
            or not getattr(self.user, "is_authenticated", False)
        ):
            raise ValidationError(
                "An authenticated user is required."
            )

        budget = super().save(commit=False)
        budget.user = self.user

        if commit:
            budget.save()

        return budget