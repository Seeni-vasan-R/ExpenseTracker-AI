from django import forms
from django.db.models import Q

from .models import (
    Category,
    Transaction,
    RecurringTransaction,
)


class StyledModelForm(forms.ModelForm):
    """
    Base form to automatically apply Bootstrap classes.
    """

    DATE_FIELDS = {"transaction_date", "start_date", "end_date"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
                continue

            css = "form-select" if isinstance(
                field.widget,
                (forms.Select, forms.SelectMultiple)
            ) else "form-control"

            field.widget.attrs.setdefault("class", css)

            if name in self.DATE_FIELDS:
                field.widget.input_type = "date"


class CategoryForm(StyledModelForm):

    class Meta:
        model = Category
        fields = [
            "name",
            "category_type",
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        category = super().save(commit=False)

        category.user = self.user
        category.is_default = False

        if commit:
            category.save()

        return category


class TransactionForm(StyledModelForm):

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "category",
            "amount",
            "payment_method",
            "transaction_date",
            "description",
            "receipt",
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        # IMPORTANT FIX
        if user:
            self.instance.user = user

            self.fields["category"].queryset = (
                Category.objects.filter(
                    Q(user=user) | Q(is_default=True)
                ).order_by("name")
            )

    def save(self, commit=True):
        transaction = super().save(commit=False)

        transaction.user = self.user

        if commit:
            transaction.save()

        return transaction


class RecurringTransactionForm(StyledModelForm):

    class Meta:
        model = RecurringTransaction
        fields = [
            "transaction_type",
            "category",
            "amount",
            "payment_method",
            "description",
            "frequency",
            "start_date",
            "end_date",
            "is_active",
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user:
            self.fields["category"].queryset = (
                Category.objects.filter(
                    Q(user=user) | Q(is_default=True)
                ).order_by("name")
            )

    def save(self, commit=True):
        recurring = super().save(commit=False)

        recurring.user = self.user

        if not recurring.next_occurrence:
            recurring.next_occurrence = recurring.start_date

        if commit:
            recurring.save()

        return recurring