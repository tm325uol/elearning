from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import OpenApiParameter, extend_schema

from .serializers import UserProfileSerializer, UserSearchResponseSerializer

User = get_user_model()


def get_user_data_payload(user):
    data = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name or user.username,
        "role": user.get_role_display(),
        "email": user.email,
        "location": user.location or "—",
        "joined": user.date_joined.strftime("%B %Y"),
        "bio": user.bio or "No bio available.",
        "avatar_url": user.avatar_url,
    }

    if user.is_teacher:
        data["teaching_courses"] = [
            {
                "id": teaching.course.id,
                "title": teaching.course.title,
            }
            for teaching in user.teachings.select_related("course").all()
        ]
        data["enrolled_courses"] = None
    else:
        data["teaching_courses"] = None
        data["enrolled_courses"] = user.enrollments.count()

    return data


@extend_schema(
    summary="Search users",
    description="Search active users by name, username, or email, with optional role filtering.",
    parameters=[
        OpenApiParameter(name="q", type=str, required=False),
        OpenApiParameter(name="role", type=str, required=False),
    ],
    responses=UserSearchResponseSerializer,
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_search_api(request):
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").upper()

    users = User.objects.filter(is_active=True)

    if role and role != "ALL":
        users = users.filter(role=role)

    if query:
        users = users.filter(
            Q(full_name__icontains=query)
            | Q(username__icontains=query)
            | Q(email__icontains=query)
        )

    payload = [get_user_data_payload(user) for user in users[:15]]
    return Response({"results": payload})


@extend_schema(
    summary="Get user profile",
    description="Return the public profile payload for a user by username.",
    responses=UserProfileSerializer,
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile_api(request, username):
    profile_user = get_object_or_404(User, username=username)
    payload = get_user_data_payload(profile_user)
    return Response(payload)