from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",
        "notification_type",
        "message",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = (
        "message",
        "recipient__username",
        "recipient__email",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("recipient",)