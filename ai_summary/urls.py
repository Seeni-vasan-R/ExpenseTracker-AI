from django.urls import path

from . import views


app_name = "ai_summary"


urlpatterns = [
    path(
        "",
        views.summary_page,
        name="summary",
    ),
    path(
        "api/",
        views.summary_api,
        name="summary-api",
    ),
    path(
        "api/latest/",
        views.latest_summary_api,
        name="latest-api",
    ),
]