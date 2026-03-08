from rest_framework import serializers

from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    # Format the time nicely for the frontend (e.g., "Oct 24, 2:30 PM")
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'message', 'link', 'is_read', 'time_ago']

    def get_time_ago(self, obj):
        return obj.created_at.strftime("%b %d, %I:%M %p")
