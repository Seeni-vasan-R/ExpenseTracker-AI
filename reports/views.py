from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .forms import ReportFilterForm
from .services import ReportService


class ReportDashboardView(LoginRequiredMixin, TemplateView):

    template_name = "reports/report_dashboard.html"
    login_url = "accounts:login"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        service = ReportService(self.request.user)

        context["summary"] = service.get_summary()

        context["monthly_report"] = (
            service.monthly_report()
        )

        context["category_report"] = (
            service.category_report()
        )

        context["payment_report"] = (
            service.payment_method_report()
        )

        context["recent_transactions"] = (
            service.recent_transactions()
        )

        context["filter_form"] = ReportFilterForm(
            self.request.GET
        )

        return context