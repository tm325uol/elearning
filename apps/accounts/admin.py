from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "username",
        "full_name",
        "email",
        "role",
        "location",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    )
    search_fields = (
        "username",
        "full_name",
        "email",
        "location",
    )
    ordering = ("username",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Profile Info",
            {
                "fields": (
                    "role",
                    "full_name",
                    "location",
                    "profile_photo",
                    "bio",
                )
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Profile Info",
            {
                "classes": ("wide",),
                "fields": (
                    "role",
                    "full_name",
                    "email",
                    "location",
                    "profile_photo",
                    "bio",
                ),
            },
        ),
    )