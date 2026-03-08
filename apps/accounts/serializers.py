from rest_framework import serializers


class CourseMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    role = serializers.CharField()
    email = serializers.EmailField()
    location = serializers.CharField()
    joined = serializers.CharField()
    bio = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True, required=False)
    teaching_courses = CourseMiniSerializer(many=True, required=False, allow_null=True)
    enrolled_courses = serializers.IntegerField(required=False, allow_null=True)


class UserSearchResponseSerializer(serializers.Serializer):
    results = UserProfileSerializer(many=True)
