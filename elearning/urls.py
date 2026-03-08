from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Web pages
    path("", include("apps.core.urls")),
    path("", include("apps.accounts.urls")),
    path("courses/", include("apps.courses.urls")),
    path("status/", include("apps.status.urls")),
    path("chat/", include("apps.chat.urls")),

    # Central API gateway
    path("api/", include("apps.api.urls")),
]

# Serve uploaded media files such as profile images and course materials in development only
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
