from django.urls import path
from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import api_home

app_name = "api"

urlpatterns = [
    path("", api_home, name="home"),
    path("schema/", SpectacularJSONAPIView.as_view(), name="schema"),
    path("docs/swagger/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger"),
    path("docs/redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]
