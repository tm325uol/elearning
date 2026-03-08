from django.urls import include, path
from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import api_home

app_name = "api"

urlpatterns = [
    # API landing page
    path("", api_home, name="home"),

    # API documentation
    path("schema/", SpectacularJSONAPIView.as_view(), name="schema"),
    path(
        "docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="swagger",
    ),
    path(
        "docs/redoc/",
        SpectacularRedocView.as_view(url_name="api:schema"),
        name="redoc",
    ),

    # Feature APIs
    path("users/", include("apps.accounts.api_urls")),
    path("notifications/", include("apps.notifications.api_urls")),
]