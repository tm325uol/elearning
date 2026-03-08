from django.shortcuts import get_object_or_404

from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import Notification
from .serializers import (
    NotificationListResponseSerializer,
    NotificationSerializer,
    SuccessSerializer,
)


class GetNotificationsAPI(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List notifications",
        description="Return the latest notifications for the authenticated user.",
        responses=NotificationListResponseSerializer,
    )
    def get(self, request):
        # Fetch the latest 30 notifications, BOTH read and unread
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:30]
        
        serializer = NotificationSerializer(notifications, many=True)

        return Response(
            {
                "unread_count": Notification.objects.filter(
                    recipient=request.user,
                    is_read=False,
                ).count(),
                "notifications": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class MarkNotificationReadAPI(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark notification as read",
        request=None,
        responses=SuccessSerializer,
    )
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user,
        )
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"success": True}, status=status.HTTP_200_OK)


class MarkAllNotificationsReadAPI(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark all notifications as read",
        request=None,
        responses=SuccessSerializer,
    )
    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return Response({"success": True}, status=status.HTTP_200_OK)


class DeleteNotificationAPI(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Delete notification",
        request=None,
        responses=SuccessSerializer,
    )
    def delete(self, request, pk):
        deleted, _ = Notification.objects.filter(
            id=pk,
            recipient=request.user,
        ).delete()

        if deleted:
            return Response({"success": True}, status=status.HTTP_200_OK)

        return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)


class MarkNotificationUnreadAPI(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark notification as unread",
        request=None,
        responses=SuccessSerializer,
    )
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user,
        )
        notification.is_read = False
        notification.save(update_fields=["is_read"])

        return Response({"success": True}, status=status.HTTP_200_OK)