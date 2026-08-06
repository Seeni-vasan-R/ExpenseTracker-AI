from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth

from transactions.models import Transaction


class ReportService:

    def __init__(self, user):

        self.user = user

        self.transactions = (
            Transaction.objects.active()
            .filter(user=user)
        )

    def get_summary(self):

        income = (
            self.transactions.filter(
                transaction_type="Income"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        expense = (
            self.transactions.filter(
                transaction_type="Expense"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        return {

            "income": income,

            "expense": expense,

            "balance": income - expense,

            "transactions": self.transactions.count(),

        }

    def monthly_report(self):

        return (

            self.transactions

            .annotate(
                month=TruncMonth("transaction_date")
            )

            .values("month")

            .annotate(

                income=Sum(
                    "amount",
                    filter=Q(
                        transaction_type="Income"
                    )
                ),

                expense=Sum(
                    "amount",
                    filter=Q(
                        transaction_type="Expense"
                    )
                ),

            )

            .order_by("month")

        )

    def category_report(self):

        return (

            self.transactions

            .filter(
                transaction_type="Expense"
            )

            .values(
                "category__name"
            )

            .annotate(

                total=Sum("amount")

            )

            .order_by("-total")

        )

    def payment_method_report(self):

        return (

            self.transactions

            .values(
                "payment_method"
            )

            .annotate(

                total=Sum("amount")

            )

            .order_by("-total")

        )

    def recent_transactions(self):

        return (

            self.transactions

            .select_related(
                "category"
            )

            .order_by(

                "-transaction_date",

                "-created_at"

            )[:10]

        )