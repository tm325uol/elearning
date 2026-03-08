from django.contrib import admin
from .models import (
    Course,
    CourseMaterial,
    Teaching,
    Enrollment,
    CourseFeedback,
    Deadline,
)


# =========================
# Inline admins
# =========================
class TeachingInline(admin.TabularInline):
    model = Teaching
    extra = 0
    autocomplete_fields = ("teacher",)


class DeadlineInline(admin.TabularInline):
    model = Deadline
    extra = 0
    fields = ("title", "due_at", "created_at")
    readonly_fields = ("created_at",)


class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 0
    fields = ("original_name", "file", "uploaded_by", "uploaded_at")
    readonly_fields = ("original_name", "uploaded_at")
    autocomplete_fields = ("uploaded_by",)


# =========================
# Course
# =========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "course_id",
        "title",
        "category",
        "duration",
        "max_students",
        "student_count_display",
        "is_full_display",
        "updated_at",
    )
    list_filter = ("category", "created_at", "updated_at")
    search_fields = ("course_id", "title", "description")
    ordering = ("-updated_at", "title")
    readonly_fields = (
        "created_at",
        "updated_at",
        "student_count_display",
        "is_full_display",
    )
    inlines = [TeachingInline, CourseMaterialInline, DeadlineInline]

    fieldsets = (
        (
            "Course Information",
            {
                "fields": (
                    "course_id",
                    "title",
                    "description",
                    "category",
                )
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "duration",
                    "max_students",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "student_count_display",
                    "is_full_display",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Students")
    def student_count_display(self, obj):
        return obj.student_count

    @admin.display(boolean=True, description="Full")
    def is_full_display(self, obj):
        return obj.is_full


# =========================
# Course Material
# =========================
@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "original_name",
        "course",
        "uploaded_by",
        "extension",
        "uploaded_at",
    )
    list_filter = ("uploaded_at", "course__category")
    search_fields = (
        "original_name",
        "course__course_id",
        "course__title",
        "uploaded_by__username",
        "uploaded_by__full_name",
    )
    ordering = ("-uploaded_at",)
    readonly_fields = ("original_name", "extension", "uploaded_at")
    autocomplete_fields = ("course", "uploaded_by")


# =========================
# Teaching
# =========================
@admin.register(Teaching)
class TeachingAdmin(admin.ModelAdmin):
    list_display = ("teacher", "course")
    search_fields = (
        "teacher__username",
        "teacher__full_name",
        "course__course_id",
        "course__title",
    )
    autocomplete_fields = ("teacher", "course")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = db_field.remote_field.model.objects.filter(role="TEACHER")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# =========================
# Enrollment
# =========================
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "progress",
        "grade",
        "created_at",
    )
    list_filter = ("created_at", "course__category")
    search_fields = (
        "student__username",
        "student__full_name",
        "course__course_id",
        "course__title",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("student", "course")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = db_field.remote_field.model.objects.filter(role="STUDENT")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# =========================
# Course Feedback
# =========================
@admin.register(CourseFeedback)
class CourseFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "rating",
        "created_at",
    )
    list_filter = ("rating", "created_at", "course__category")
    search_fields = (
        "student__username",
        "student__full_name",
        "course__course_id",
        "course__title",
        "comment",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("student", "course")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = db_field.remote_field.model.objects.filter(role="STUDENT")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# =========================
# Deadline
# =========================
@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "due_at",
        "status_display",
        "created_at",
    )
    list_filter = ("due_at", "created_at", "course__category")
    search_fields = (
        "title",
        "description",
        "course__course_id",
        "course__title",
    )
    ordering = ("due_at",)
    readonly_fields = ("created_at", "status_display")
    autocomplete_fields = ("course",)

    @admin.display(description="Status")
    def status_display(self, obj):
        return obj.status()
