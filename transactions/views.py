from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    CategoryForm,
    TransactionForm,
)
from .models import (
    Category,
    Transaction,
)


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = (
        "transactions/transaction_list.html"
    )
    context_object_name = "transactions"
    paginate_by = 10
    login_url = "accounts:login"

    def get_queryset(self):
        queryset = (
            Transaction.objects
            .active()
            .for_user(self.request.user)
            .select_related("category")
            .order_by(
                "-transaction_date",
                "-transaction_time",
                "-created_at",
            )
        )

        search = self.request.GET.get(
            "search",
            "",
        ).strip()

        transaction_type = self.request.GET.get(
            "type",
            "",
        ).strip()

        category_id = self.request.GET.get(
            "category",
            "",
        ).strip()

        payment_method = self.request.GET.get(
            "payment_method",
            "",
        ).strip()

        date_from = self.request.GET.get(
            "date_from",
            "",
        ).strip()

        date_to = self.request.GET.get(
            "date_to",
            "",
        ).strip()

        min_amount = self.request.GET.get(
            "min_amount",
            "",
        ).strip()

        max_amount = self.request.GET.get(
            "max_amount",
            "",
        ).strip()

        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(category__name__icontains=search)
                | Q(payment_method__icontains=search)
                | Q(transaction_type__icontains=search)
            )

        if transaction_type in {
            "Income",
            "Expense",
        }:
            queryset = queryset.filter(
                transaction_type=transaction_type,
            )

        if category_id.isdigit():
            queryset = queryset.filter(
                category_id=int(category_id),
            )

        if payment_method:
            queryset = queryset.filter(
                payment_method=payment_method,
            )

        if date_from:
            queryset = queryset.filter(
                transaction_date__gte=date_from,
            )

        if date_to:
            queryset = queryset.filter(
                transaction_date__lte=date_to,
            )

        min_amount_value = self.parse_decimal(
            min_amount,
        )

        if min_amount_value is not None:
            queryset = queryset.filter(
                amount__gte=min_amount_value,
            )

        max_amount_value = self.parse_decimal(
            max_amount,
        )

        if max_amount_value is not None:
            queryset = queryset.filter(
                amount__lte=max_amount_value,
            )

        return queryset

    @staticmethod
    def parse_decimal(value):
        if not value:
            return None

        try:
            number = Decimal(value)

            if number < 0:
                return None

            return number

        except (
            InvalidOperation,
            ValueError,
        ):
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(
            **kwargs,
        )

        filtered_transactions = self.get_queryset()

        total_income = (
            filtered_transactions
            .filter(
                transaction_type="Income",
            )
            .aggregate(
                total=Sum("amount"),
            )
            .get("total")
            or Decimal("0.00")
        )

        total_expense = (
            filtered_transactions
            .filter(
                transaction_type="Expense",
            )
            .aggregate(
                total=Sum("amount"),
            )
            .get("total")
            or Decimal("0.00")
        )

        categories = (
            Category.objects.filter(
                Q(user=self.request.user)
                | Q(
                    user__isnull=True,
                    is_default=True,
                )
            )
            .order_by(
                "category_type",
                "name",
            )
        )

        context.update(
            {
                "search": self.request.GET.get(
                    "search",
                    "",
                ),
                "selected_type": (
                    self.request.GET.get(
                        "type",
                        "",
                    )
                ),
                "selected_category": (
                    self.request.GET.get(
                        "category",
                        "",
                    )
                ),
                "selected_payment_method": (
                    self.request.GET.get(
                        "payment_method",
                        "",
                    )
                ),
                "selected_date_from": (
                    self.request.GET.get(
                        "date_from",
                        "",
                    )
                ),
                "selected_date_to": (
                    self.request.GET.get(
                        "date_to",
                        "",
                    )
                ),
                "selected_min_amount": (
                    self.request.GET.get(
                        "min_amount",
                        "",
                    )
                ),
                "selected_max_amount": (
                    self.request.GET.get(
                        "max_amount",
                        "",
                    )
                ),
                "categories": categories,
                "payment_methods": (
                    Transaction.PAYMENT_METHODS
                ),
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": (
                    total_income - total_expense
                ),
                "transaction_count": (
                    filtered_transactions.count()
                ),
            }
        )

        return context


class TransactionCreateView(
    LoginRequiredMixin,
    CreateView,
):
    model = Transaction
    form_class = TransactionForm
    template_name = (
        "transactions/transaction_form.html"
    )
    success_url = reverse_lazy(
        "transactions:transaction_list",
    )
    login_url = "accounts:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        with db_transaction.atomic():
            response = super().form_valid(form)

        messages.success(
            self.request,
            "Transaction created successfully.",
        )

        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below.",
        )

        return super().form_invalid(form)


class TransactionUpdateView(
    LoginRequiredMixin,
    UpdateView,
):
    model = Transaction
    form_class = TransactionForm
    template_name = (
        "transactions/transaction_form.html"
    )
    success_url = reverse_lazy(
        "transactions:transaction_list",
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Transaction.objects
            .active()
            .for_user(self.request.user)
            .select_related("category")
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        with db_transaction.atomic():
            response = super().form_valid(form)

        messages.success(
            self.request,
            "Transaction updated successfully.",
        )

        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below.",
        )

        return super().form_invalid(form)


class TransactionDetailView(
    LoginRequiredMixin,
    DetailView,
):
    model = Transaction
    template_name = (
        "transactions/transaction_detail.html"
    )
    context_object_name = "transaction"
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Transaction.objects
            .active()
            .for_user(self.request.user)
            .select_related("category")
        )


class TransactionDeleteView(
    LoginRequiredMixin,
    DeleteView,
):
    model = Transaction
    template_name = (
        "transactions/transaction_confirm_delete.html"
    )
    success_url = reverse_lazy(
        "transactions:transaction_list",
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Transaction.objects
            .active()
            .for_user(self.request.user)
            .select_related("category")
        )

    def post(self, request, *args, **kwargs):
        transaction_object = self.get_object()

        transaction_object.soft_delete()

        messages.success(
            request,
            "Transaction deleted successfully.",
        )

        return redirect(self.success_url)


class RestoreTransactionView(
    LoginRequiredMixin,
    View,
):
    login_url = "accounts:login"

    def post(self, request, pk):
        transaction_object = get_object_or_404(
            Transaction.objects
            .deleted()
            .for_user(request.user)
            .select_related("category"),
            pk=pk,
        )

        transaction_object.restore()

        messages.success(
            request,
            "Transaction restored successfully.",
        )

        return redirect(
            "transactions:transaction_list",
        )


class CategoryListView(
    LoginRequiredMixin,
    ListView,
):
    model = Category
    template_name = (
        "transactions/category_list.html"
    )
    context_object_name = "categories"
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Category.objects.filter(
                Q(user=self.request.user)
                | Q(
                    user__isnull=True,
                    is_default=True,
                )
            )
            .order_by(
                "category_type",
                "name",
            )
        )


class CategoryCreateView(
    LoginRequiredMixin,
    CreateView,
):
    model = Category
    form_class = CategoryForm
    template_name = (
        "transactions/category_form.html"
    )
    success_url = reverse_lazy(
        "transactions:category_list",
    )
    login_url = "accounts:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        with db_transaction.atomic():
            response = super().form_valid(form)

        messages.success(
            self.request,
            "Category created successfully.",
        )

        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below.",
        )

        return super().form_invalid(form)


class CategoryUpdateView(
    LoginRequiredMixin,
    UpdateView,
):
    model = Category
    form_class = CategoryForm
    template_name = (
        "transactions/category_form.html"
    )
    success_url = reverse_lazy(
        "transactions:category_list",
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return Category.objects.filter(
            user=self.request.user,
            is_default=False,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        with db_transaction.atomic():
            response = super().form_valid(form)

        messages.success(
            self.request,
            "Category updated successfully.",
        )

        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below.",
        )

        return super().form_invalid(form)


class CategoryDeleteView(
    LoginRequiredMixin,
    DeleteView,
):
    model = Category
    template_name = (
        "transactions/category_confirm_delete.html"
    )
    success_url = reverse_lazy(
        "transactions:category_list",
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return Category.objects.filter(
            user=self.request.user,
            is_default=False,
        )

    def post(self, request, *args, **kwargs):
        category = self.get_object()

        try:
            with db_transaction.atomic():
                category.delete()

        except ProtectedError:
            messages.error(
                request,
                (
                    "This category cannot be deleted "
                    "because it is currently used "
                    "by a transaction."
                ),
            )

        else:
            messages.success(
                request,
                "Category deleted successfully.",
            )

        return redirect(self.success_url)