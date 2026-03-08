from django.urls import include, path
from django.contrib.admin.views.decorators import staff_member_required
from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import api_home

app_name = "api"

urlpatterns = [
    path("", staff_member_required(api_home), name="home"),
    path("schema/", staff_member_required(SpectacularJSONAPIView.as_view()), name="schema"),
    path(
        "docs/swagger/",
        staff_member_required(SpectacularSwaggerView.as_view(url_name="api:schema")),
        name="swagger",
    ),
    path(
        "docs/redoc/",
        staff_member_required(SpectacularRedocView.as_view(url_name="api:schema")),
        name="redoc",
    ),

    # Feature APIs
    path("users/", include("apps.accounts.api_urls")),
    path("notifications/", include("apps.notifications.api_urls")),
]