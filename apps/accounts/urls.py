from django.urls import path

from . import api
from . import views

app_name = "accounts"

urlpatterns = [
    # --- Authentication ---
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # --- Dashboards & Profiles ---
    # The redirect link (e.g., clicking the logo)
    path("home/", views.dashboard_redirect, name="home"),
    
    # The endpoint for saving the profile edit form
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    
    # The unified Dashboard / Public Profile View
    path("@<str:username>/", views.user_profile, name="user_profile"),

    # --- API for User Data ---
    path("api/users/search/", api.user_search_api, name="user_search_api"),
    path("api/users/<str:username>/", api.user_profile_api, name="user_profile_api")
]
