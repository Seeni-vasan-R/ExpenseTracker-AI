from django import forms
from django.db.models import Q

from .models import Budget
from transactions.models import Category


class BudgetForm(forms.ModelForm):

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
            "start_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

        if user:
            self.instance.user = user

            self.fields["category"].queryset = (
                Category.objects.filter(
                    (
                        Q(user=user) |
                        Q(is_default=True)
                    )
                    & ~Q(category_type="Income")
                ).order_by("name")
            )

            self.fields["category"].required = False

    def save(self, commit=True):
        budget = super().save(commit=False)

        budget.user = self.user

        if commit:
            budget.save()

        return budget