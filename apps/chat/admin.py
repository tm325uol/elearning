from django.contrib import admin

from .models import Conversation, Message, UserBlock


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("sender", "content", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("sender",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "participant_list", "created_at", "updated_at", "message_count")
    list_filter = ("created_at", "updated_at")
    search_fields = ("participants__username", "participants__email")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("participants",)
    inlines = [MessageInline]

    def participant_list(self, obj):
        return ", ".join(obj.participants.values_list("username", flat=True))
    participant_list.short_description = "Participants"

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "short_content", "created_at", "cleared_by_count")
    list_filter = ("created_at",)
    search_fields = (
        "content",
        "sender__username",
        "sender__email",
        "conversation__id",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("conversation", "sender")
    filter_horizontal = ("cleared_by",)

    def short_content(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
    short_content.short_description = "Content"

    def cleared_by_count(self, obj):
        return obj.cleared_by.count()
    cleared_by_count.short_description = "Cleared by"


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ("id", "blocker", "blocked", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "blocker__username",
        "blocker__email",
        "blocked__username",
        "blocked__email",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("blocker", "blocked")