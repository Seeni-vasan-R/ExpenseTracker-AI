from django.urls import path

from . import views


app_name = "analytics"


urlpatterns = [
    path(
        "",
        views.dashboard_page,
        name="dashboard",
    ),
    path(
        "api/dashboard/",
        views.dashboard_api,
        name="dashboard-api",
    ),
    path(
        "charts/categories/",
        views.category_chart,
        name="category-chart",
    ),
    path(
        "charts/timeline/",
        views.timeline_chart,
        name="timeline-chart",
    ),
    path(
        "charts/month-view/",
        views.month_view_chart,
        name="month-view-chart",
    ),
    path(
        "charts/expense-calendar/",
        views.expense_calendar_chart,
        name="expense-calendar-chart",
    ),
    path(
        "forecast/features/",
        views.forecast_features,
        name="forecast-features",
    ),
]