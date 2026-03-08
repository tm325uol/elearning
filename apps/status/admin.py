from django.contrib import admin

from .models import StatusUpdate, Comment, Like


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "content", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)


class LikeInline(admin.TabularInline):
    model = Like
    extra = 0
    fields = ("user", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "short_content", "created_at", "updated_at", "comment_count", "like_count")
    list_filter = ("created_at", "updated_at")
    search_fields = ("content", "author__username", "author__full_name", "author__email")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("author",)
    inlines = [CommentInline, LikeInline]

    def short_content(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
    short_content.short_description = "Content"

    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = "Comments"

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = "Likes"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "status_update", "short_content", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "content",
        "author__username",
        "author__full_name",
        "author__email",
        "status_update__content",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author", "status_update")

    def short_content(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
    short_content.short_description = "Content"


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status_update", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "user__username",
        "user__full_name",
        "user__email",
        "status_update__content",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user", "status_update")