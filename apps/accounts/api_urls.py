from django.urls import path

from . import api

app_name = "accounts_api"

urlpatterns = [
    path("search/", api.UserSearchAPI.as_view(), name="search"),
    path("<str:username>/", api.UserProfileAPI.as_view(), name="detail"),
]