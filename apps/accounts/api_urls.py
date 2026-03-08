from django.urls import path
from . import api

app_name = "accounts_api"

urlpatterns = [
    path("search/", api.user_search_api, name="user_search_api"),
    path("<str:username>/", api.user_profile_api, name="user_profile_api")
]