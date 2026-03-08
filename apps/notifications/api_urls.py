from django.urls import path
from . import api

app_name = "notifications_api"

urlpatterns = [
    path("", api.GetNotificationsAPI.as_view(), name="list"),
    path("<int:pk>/read/", api.MarkNotificationReadAPI.as_view(), name="mark_read"),
    path("read-all/", api.MarkAllNotificationsReadAPI.as_view(), name="mark_all_read"),
    path("<int:pk>/unread/", api.MarkNotificationUnreadAPI.as_view(), name="mark_unread"),
    path("<int:pk>/delete/", api.DeleteNotificationAPI.as_view(), name="delete"),
]
