from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    # Human-friendly timestamp for the frontend
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "message",
            "link",
            "is_read",
            "time_ago",
        ]

    def get_time_ago(self, obj) -> str:
        return obj.created_at.strftime("%b %d, %I:%M %p")


class NotificationListResponseSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
    notifications = NotificationSerializer(many=True)


class SuccessSerializer(serializers.Serializer):
    success = serializers.BooleanField()