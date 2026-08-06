from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DetailView,
    DeleteView,
)

from .models import (
    Transaction,
    Category,
    RecurringTransaction,
)

from .forms import (
    TransactionForm,
    CategoryForm,
    RecurringTransactionForm,
)


class TransactionListView(LoginRequiredMixin, ListView):
    """
    Display all active transactions.
    """

    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 10
    login_url = "accounts:login"

    def get_queryset(self):
        queryset = (
            Transaction.objects.active()
            .filter(user=self.request.user)
            .select_related("category")
            .order_by("-transaction_date", "-created_at")
        )

        search = self.request.GET.get("search", "")

        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(category__name__icontains=search)
                | Q(payment_method__icontains=search)
                | Q(transaction_type__icontains=search)
            )

        transaction_type = self.request.GET.get("type")

        if transaction_type:
            queryset = queryset.filter(
                transaction_type=transaction_type
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        transactions = self.get_queryset()

        context["search"] = self.request.GET.get("search", "")
        context["selected_type"] = self.request.GET.get("type", "")

        context["total_income"] = (
            transactions.filter(
                transaction_type="Income"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        context["total_expense"] = (
            transactions.filter(
                transaction_type="Expense"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        context["balance"] = (
            context["total_income"]
            - context["total_expense"]
        )

        context["transaction_count"] = (
            transactions.count()
        )

        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new transaction.
    """

    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"
    success_url = reverse_lazy(
        "transactions:transaction_list"
    )
    login_url = "accounts:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # IMPORTANT
        form.instance.user = self.request.user

        messages.success(
            self.request,
            "Transaction created successfully."
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below."
        )

        return super().form_invalid(form)

class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing transaction.
    """

    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"
    success_url = reverse_lazy(
        "transactions:transaction_list"
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Transaction.objects.active()
            .filter(user=self.request.user)
            .select_related("category")
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # IMPORTANT
        form.instance.user = self.request.user

        messages.success(
            self.request,
            "Transaction updated successfully."
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below."
        )

        return super().form_invalid(form)


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """
    Display details of a transaction.
    """

    model = Transaction
    template_name = "transactions/transaction_detail.html"
    context_object_name = "transaction"
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Transaction.objects.active()
            .filter(user=self.request.user)
            .select_related("category")
        )


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Soft delete a transaction.
    """

    model = Transaction
    success_url = reverse_lazy(
        "transactions:transaction_list"
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Transaction.objects.active()
            .filter(user=self.request.user)
        )

    def post(self, request, *args, **kwargs):
        transaction = self.get_object()

        transaction.soft_delete()

        messages.success(
            request,
            "Transaction deleted successfully."
        )

        return redirect(self.success_url)


class RestoreTransactionView(LoginRequiredMixin, View):
    """
    Restore a soft deleted transaction.
    """

    login_url = "accounts:login"

    def post(self, request, pk):

        transaction = get_object_or_404(
            Transaction,
            pk=pk,
            user=request.user,
            is_deleted=True,
        )

        transaction.restore()

        messages.success(
            request,
            "Transaction restored successfully."
        )

        return redirect(
            "transactions:transaction_list"
        )
        
class CategoryListView(LoginRequiredMixin, ListView):
    """
    Display default and user-created categories.
    """

    model = Category
    template_name = "transactions/category_list.html"
    context_object_name = "categories"
    login_url = "accounts:login"

    def get_queryset(self):
        return (
            Category.objects.filter(
                Q(user=self.request.user) |
                Q(is_default=True)
            ).order_by(
                "category_type",
                "name"
            )
        )


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new category.
    """

    model = Category
    form_class = CategoryForm
    template_name = "transactions/category_form.html"
    success_url = reverse_lazy(
        "transactions:category_list"
    )
    login_url = "accounts:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        messages.success(
            self.request,
            "Category created successfully."
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below."
        )

        return super().form_invalid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing category.
    """

    model = Category
    form_class = CategoryForm
    template_name = "transactions/category_form.html"
    success_url = reverse_lazy(
        "transactions:category_list"
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return Category.objects.filter(
            user=self.request.user
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user

        messages.success(
            self.request,
            "Category updated successfully."
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below."
        )

        return super().form_invalid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a category.
    """

    model = Category
    success_url = reverse_lazy(
        "transactions:category_list"
    )
    login_url = "accounts:login"

    def get_queryset(self):
        return Category.objects.filter(
            user=self.request.user
        )

    def post(self, request, *args, **kwargs):
        category = self.get_object()

        try:
            category.delete()

            messages.success(
                request,
                "Category deleted successfully."
            )

        except ProtectedError:
            messages.error(
                request,
                "Cannot delete this category because it is being used by transactions."
            )

        return redirect(self.success_url)