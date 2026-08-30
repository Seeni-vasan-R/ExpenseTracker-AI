"""
URL configuration for the expense_tracker project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "accounts/",
        include("accounts.urls"),
    ),

    path(
        "dashboard/",
        include("dashboard.urls"),
    ),

    path(
        "transactions/",
        include("transactions.urls"),
    ),

    path(
        "budget/",
        include("budget.urls"),
    ),

    path(
        "analytics/",
        include("analytics.urls"),
    ),

    path(
        "ai-summary/",
        include("ai_summary.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )