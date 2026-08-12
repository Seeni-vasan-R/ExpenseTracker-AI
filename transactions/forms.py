from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from .models import (
    Category,
    RecurringTransaction,
    Transaction,
)


class StyledModelForm(forms.ModelForm):
    DATE_FIELDS = {
        "transaction_date",
        "start_date",
        "end_date",
        "next_occurrence",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault(
                    "class",
                    "form-check-input",
                )
                continue

            if isinstance(
                widget,
                (
                    forms.Select,
                    forms.SelectMultiple,
                    forms.RadioSelect,
                ),
            ):
                css_class = "form-select"
            else:
                css_class = "form-control"

            widget.attrs.setdefault("class", css_class)

            if name in self.DATE_FIELDS:
                widget.input_type = "date"
                widget.format = "%Y-%m-%d"
                field.input_formats = ["%Y-%m-%d"]


class UserOwnedFormMixin:
    user = None

    def validate_user(self):
        if self.user is None:
            raise ValidationError(
                "An authenticated user is required."
            )

        if not self.user.is_authenticated:
            raise ValidationError(
                "An authenticated user is required."
            )

    def validate_existing_object_owner(self):
        instance = getattr(self, "instance", None)

        if (
            instance
            and instance.pk
            and hasattr(instance, "user_id")
            and instance.user_id != self.user.id
        ):
            raise ValidationError(
                "You are not allowed to modify this record."
            )


class CategoryForm(UserOwnedFormMixin, StyledModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
            "category_type",
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = " ".join(
            self.cleaned_data["name"].split()
        )

        if not name:
            raise ValidationError(
                "Category name cannot be empty."
            )

        return name

    def clean(self):
        cleaned_data = super().clean()

        self.validate_user()
        self.validate_existing_object_owner()

        name = cleaned_data.get("name")

        if name and self.user:
            duplicate_categories = Category.objects.filter(
                user=self.user,
                name__iexact=name,
                is_default=False,
            )

            if self.instance and self.instance.pk:
                duplicate_categories = (
                    duplicate_categories.exclude(
                        pk=self.instance.pk
                    )
                )

            if duplicate_categories.exists():
                self.add_error(
                    "name",
                    "You already have a category with this name.",
                )

        return cleaned_data

    def save(self, commit=True):
        self.validate_user()

        category = super().save(commit=False)
        category.user = self.user
        category.is_default = False

        if commit:
            category.save()

        return category


class TransactionForm(UserOwnedFormMixin, StyledModelForm):
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

        widgets = {
            "transaction_type": forms.RadioSelect(
                attrs={
                    "class": "transaction-type-radio",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional description",
                }
            ),
            "receipt": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*,.pdf",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        self.fields["transaction_type"].choices = [
            ("Income", "Income"),
            ("Expense", "Expense"),
        ]

        self.fields["transaction_type"].label = (
            "Transaction type"
        )

        self.fields["category"].label = "Category"
        self.fields["amount"].label = "Amount"
        self.fields["payment_method"].label = (
            "Payment method"
        )
        self.fields["transaction_date"].label = "Date"
        self.fields["description"].label = "Description"
        self.fields["receipt"].label = "Receipt"

        if self.user and self.user.is_authenticated:
            self.fields["category"].queryset = (
                Category.objects.filter(
                    Q(user=self.user)
                    | Q(
                        user__isnull=True,
                        is_default=True,
                    )
                )
                .order_by("category_type", "name")
            )
        else:
            self.fields["category"].queryset = (
                Category.objects.none()
            )

    def clean_transaction_date(self):
        transaction_date = self.cleaned_data.get(
            "transaction_date"
        )

        if (
            transaction_date
            and transaction_date > timezone.localdate()
        ):
            raise ValidationError(
                "Transaction date cannot be in the future."
            )

        return transaction_date

    def clean_category(self):
        category = self.cleaned_data.get("category")

        if category is None:
            raise ValidationError(
                "Please select a valid category."
            )

        if (
            category.user_id is not None
            and category.user_id != self.user.id
        ):
            raise ValidationError(
                "Selected category does not belong to you."
            )

        return category

    def clean(self):
        cleaned_data = super().clean()

        self.validate_user()
        self.validate_existing_object_owner()

        transaction_type = cleaned_data.get(
            "transaction_type"
        )
        category = cleaned_data.get("category")

        if category and transaction_type == "Income":
            if category.category_type != "Income":
                self.add_error(
                    "category",
                    (
                        "Income transactions must use "
                        "an Income category."
                    ),
                )

        if category and transaction_type == "Expense":
            if category.category_type == "Income":
                self.add_error(
                    "category",
                    (
                        "Expense transactions cannot use "
                        "an Income category."
                    ),
                )

        return cleaned_data

    def save(self, commit=True):
        self.validate_user()

        transaction = super().save(commit=False)
        transaction.user = self.user

        if commit:
            transaction.save()

        return transaction


class RecurringTransactionForm(
    UserOwnedFormMixin,
    StyledModelForm,
):
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

        widgets = {
            "transaction_type": forms.RadioSelect(
                attrs={
                    "class": "transaction-type-radio",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional description",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            self.fields["category"].queryset = (
                Category.objects.filter(
                    Q(user=self.user)
                    | Q(
                        user__isnull=True,
                        is_default=True,
                    )
                )
                .order_by("category_type", "name")
            )
        else:
            self.fields["category"].queryset = (
                Category.objects.none()
            )

    def clean_category(self):
        category = self.cleaned_data.get("category")

        if category is None:
            raise ValidationError(
                "Please select a valid category."
            )

        if (
            category.user_id is not None
            and category.user_id != self.user.id
        ):
            raise ValidationError(
                "Selected category does not belong to you."
            )

        return category

    def clean(self):
        cleaned_data = super().clean()

        self.validate_user()
        self.validate_existing_object_owner()

        transaction_type = cleaned_data.get(
            "transaction_type"
        )
        category = cleaned_data.get("category")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if (
            start_date
            and end_date
            and end_date < start_date
        ):
            self.add_error(
                "end_date",
                "End date cannot be before start date.",
            )

        if category and transaction_type == "Income":
            if category.category_type != "Income":
                self.add_error(
                    "category",
                    (
                        "Income recurring transactions must use "
                        "an Income category."
                    ),
                )

        if category and transaction_type == "Expense":
            if category.category_type == "Income":
                self.add_error(
                    "category",
                    (
                        "Expense recurring transactions cannot use "
                        "an Income category."
                    ),
                )

        return cleaned_data

    def save(self, commit=True):
        self.validate_user()

        recurring = super().save(commit=False)
        recurring.user = self.user

        if not recurring.next_occurrence:
            recurring.next_occurrence = recurring.start_date

        if commit:
            recurring.save()

        return recurring