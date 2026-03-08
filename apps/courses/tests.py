import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.courses.models import (
    Course,
    CourseFeedback,
    CourseMaterial,
    Deadline,
    Enrollment,
    Teaching,
)
from apps.notifications.models import Notification

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CoursesBaseTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def create_user(self, **kwargs):
        data = {
            "username": "student1",
            "email": "student1@example.com",
            "password": "StrongPass123!",
            "full_name": "Student One",
            "role": User.Role.STUDENT,
        }
        data.update(kwargs)
        return User.objects.create_user(**data)

    def create_teacher(self, **kwargs):
        data = {
            "username": "teacher1",
            "email": "teacher1@example.com",
            "password": "StrongPass123!",
            "full_name": "Teacher One",
            "role": User.Role.TEACHER,
        }
        data.update(kwargs)
        return User.objects.create_user(**data)

    def create_course(self, teacher=None, **kwargs):
        data = {
            "course_id": "CS101",
            "title": "Intro to Testing",
            "description": "Course description",
            "category": Course.CATEGORY_GENERAL,
            "duration": "12 weeks",
            "max_students": None,
        }
        data.update(kwargs)
        course = Course.objects.create(**data)
        if teacher is not None:
            Teaching.objects.create(teacher=teacher, course=course)
        return course

    def create_enrollment(self, student=None, course=None, **kwargs):
        student = student or self.create_user()
        teacher = self.create_teacher(username="teacher_for_enrollment", email="teacher_for_enrollment@example.com")
        course = course or self.create_course(teacher=teacher, course_id="ENROLL101")

        data = {
            "student": student,
            "course": course,
            "progress": 0,
            "grade": None,
        }
        data.update(kwargs)
        return Enrollment.objects.create(**data)


class CourseModelTests(CoursesBaseTestCase):
    def test_course_student_count_and_is_full(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher, max_students=1)
        self.assertEqual(course.student_count, 0)
        self.assertFalse(course.is_full)

        self.create_enrollment(student=self.create_user(username="student2", email="student2@example.com"), course=course)
        self.assertEqual(course.student_count, 1)
        self.assertTrue(course.is_full)

    def test_course_material_save_sets_original_name_and_extension(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher)
        material = CourseMaterial.objects.create(
            course=course,
            file=SimpleUploadedFile("slides.pdf", b"pdf-bytes", content_type="application/pdf"),
            uploaded_by=teacher,
        )

        self.assertEqual(material.original_name, "slides.pdf")
        self.assertEqual(material.extension, "PDF")

    def test_deadline_status_helpers(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher)
        now = timezone.now()

        overdue = Deadline.objects.create(course=course, title="Past", due_at=now - timedelta(hours=1))
        soon = Deadline.objects.create(course=course, title="Soon", due_at=now + timedelta(hours=24))
        upcoming = Deadline.objects.create(course=course, title="Later", due_at=now + timedelta(days=5))

        self.assertTrue(overdue.is_overdue())
        self.assertEqual(overdue.status(), "due")
        self.assertTrue(soon.is_due_soon())
        self.assertEqual(soon.status(), "due_soon")
        self.assertEqual(upcoming.status(), "upcoming")


class CourseCreateViewTests(CoursesBaseTestCase):
    def test_teacher_can_create_course_with_materials(self):
        teacher = self.create_teacher()
        self.client.force_login(teacher)

        response = self.client.post(
            reverse("courses:course_create"),
            data={
                "course_id": "NEW101",
                "title": "New Course",
                "description": "A new course",
                "category": Course.CATEGORY_WEB,
                "duration": "8 weeks",
                "max_students": "25",
                "materials": [
                    SimpleUploadedFile("week1.pdf", b"week1", content_type="application/pdf"),
                    SimpleUploadedFile("week2.pdf", b"week2", content_type="application/pdf"),
                ],
            },
            HTTP_REFERER="/teacher/",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/teacher/")

        course = Course.objects.get(course_id="NEW101")
        self.assertEqual(course.title, "New Course")
        self.assertEqual(course.category, Course.CATEGORY_WEB)
        self.assertEqual(course.max_students, 25)
        self.assertTrue(Teaching.objects.filter(course=course, teacher=teacher).exists())
        self.assertEqual(CourseMaterial.objects.filter(course=course).count(), 2)

    def test_non_teacher_cannot_create_course(self):
        student = self.create_user()
        self.client.force_login(student)

        response = self.client.post(reverse("courses:course_create"), data={"title": "Blocked"})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Course.objects.count(), 0)

    def test_course_create_rejects_duplicate_course_id(self):
        teacher = self.create_teacher()
        self.create_course(teacher=teacher, course_id="DUP101")
        self.client.force_login(teacher)

        response = self.client.post(
            reverse("courses:course_create"),
            data={
                "course_id": "DUP101",
                "title": "Another Title",
                "category": Course.CATEGORY_GENERAL,
            },
            HTTP_REFERER="/teacher/",
            follow=True,
        )

        self.assertEqual(Course.objects.filter(course_id="DUP101").count(), 1)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Course ID already exists.", messages)


class CourseEnrollmentTests(CoursesBaseTestCase):
    def test_student_can_enroll_and_teacher_gets_notification(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="ENR101")
        self.client.force_login(student)

        response = self.client.post(reverse("courses:course_enroll", args=[course.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('courses:course_detail', args=[course.id])}?tab=overview")
        self.assertTrue(Enrollment.objects.filter(course=course, student=student).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=teacher,
                notification_type="ENROLLMENT",
            ).exists()
        )

    def test_teacher_cannot_enroll_in_course(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher, course_id="ENR102")
        self.client.force_login(teacher)

        response = self.client.post(
            reverse("courses:course_enroll", args=[course.id]),
            HTTP_REFERER=reverse("courses:course_detail", args=[course.id]),
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(course=course, student=teacher).exists())

    def test_student_cannot_enroll_in_course_without_teacher(self):
        student = self.create_user()
        course = self.create_course(teacher=None, course_id="NO_TCHR")
        self.client.force_login(student)

        response = self.client.post(reverse("courses:course_enroll", args=[course.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(course=course, student=student).exists())

    def test_student_cannot_enroll_when_course_is_full(self):
        teacher = self.create_teacher()
        student_a = self.create_user(username="student_a", email="student_a@example.com")
        student_b = self.create_user(username="student_b", email="student_b@example.com")
        course = self.create_course(teacher=teacher, course_id="FULL101", max_students=1)
        self.create_enrollment(student=student_a, course=course)

        self.client.force_login(student_b)
        response = self.client.post(reverse("courses:course_enroll", args=[course.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(course=course, student=student_b).exists())

    def test_second_enrollment_attempt_does_not_duplicate(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="ONCE101")
        self.create_enrollment(student=student, course=course)
        Notification.objects.all().delete()

        self.client.force_login(student)
        response = self.client.post(reverse("courses:course_enroll", args=[course.id]), follow=True)

        self.assertEqual(Enrollment.objects.filter(course=course, student=student).count(), 1)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You are already enrolled in this course.", messages)
        self.assertFalse(Notification.objects.filter(recipient=teacher, notification_type="ENROLLMENT").exists())

    def test_teacher_can_remove_enrollment(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="REM101")
        enrollment = self.create_enrollment(student=student, course=course)
        self.client.force_login(teacher)

        response = self.client.post(reverse("courses:enrollment_remove", args=[course.id, enrollment.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('courses:course_detail', args=[course.id])}?tab=students")
        self.assertFalse(Enrollment.objects.filter(id=enrollment.id).exists())

    def test_non_teacher_cannot_remove_enrollment(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="REM102")
        enrollment = self.create_enrollment(student=student, course=course)
        self.client.force_login(student)

        response = self.client.post(reverse("courses:enrollment_remove", args=[course.id, enrollment.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Enrollment.objects.filter(id=enrollment.id).exists())


class CourseFeedbackTests(CoursesBaseTestCase):
    def test_enrolled_student_can_create_feedback(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="FDBK101")
        self.create_enrollment(student=student, course=course)
        self.client.force_login(student)

        response = self.client.post(
            reverse("courses:course_feedback", args=[course.id]),
            data={
                "rating": 5,
                "comment": "Great course",
                "next": "/after-feedback/",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/after-feedback/")
        feedback = CourseFeedback.objects.get(course=course, student=student)
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.comment, "Great course")

    def test_enrolled_student_can_update_existing_feedback(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="FDBK102")
        self.create_enrollment(student=student, course=course)
        CourseFeedback.objects.create(course=course, student=student, rating=3, comment="Okay")
        self.client.force_login(student)

        response = self.client.post(
            reverse("courses:course_feedback", args=[course.id]),
            data={
                "rating": 4,
                "comment": "Better now",
                "next": "/after-feedback/",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(CourseFeedback.objects.filter(course=course, student=student).count(), 1)
        feedback = CourseFeedback.objects.get(course=course, student=student)
        self.assertEqual(feedback.rating, 4)
        self.assertEqual(feedback.comment, "Better now")

    def test_non_enrolled_student_cannot_leave_feedback(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="FDBK103")
        self.client.force_login(student)

        response = self.client.post(
            reverse("courses:course_feedback", args=[course.id]),
            data={"rating": 5, "comment": "Great", "next": "/after-feedback/"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(CourseFeedback.objects.filter(course=course, student=student).exists())

    def test_teacher_cannot_leave_feedback(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher, course_id="FDBK104")
        self.client.force_login(teacher)

        response = self.client.post(
            reverse("courses:course_feedback", args=[course.id]),
            data={"rating": 5, "comment": "Great", "next": "/after-feedback/"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(CourseFeedback.objects.count(), 0)


class CourseMaterialTests(CoursesBaseTestCase):
    def test_teacher_can_upload_material_and_students_get_notified(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="MAT101")
        self.create_enrollment(student=student, course=course)
        Notification.objects.all().delete()
        self.client.force_login(teacher)

        response = self.client.post(
            reverse("courses:material_upload", args=[course.id]),
            data={
                "material": SimpleUploadedFile(
                    "lesson1.pdf",
                    b"pdf-content",
                    content_type="application/pdf",
                )
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('courses:course_detail', args=[course.id])}?tab=materials")
        self.assertEqual(CourseMaterial.objects.filter(course=course).count(), 1)
        self.assertTrue(
            Notification.objects.filter(
                recipient=student,
                notification_type="MATERIAL",
            ).exists()
        )

    def test_material_upload_requires_file(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher, course_id="MAT102")
        self.client.force_login(teacher)

        response = self.client.post(reverse("courses:material_upload", args=[course.id]), data={}, follow=True)

        self.assertEqual(CourseMaterial.objects.filter(course=course).count(), 0)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Please choose a file to upload.", messages)

    def test_non_teacher_cannot_upload_material(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="MAT103")
        self.client.force_login(student)

        response = self.client.post(
            reverse("courses:material_upload", args=[course.id]),
            data={"material": SimpleUploadedFile("lesson1.pdf", b"pdf-content")},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(CourseMaterial.objects.filter(course=course).count(), 0)

    def test_teacher_can_delete_material(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher, course_id="MAT104")
        material = CourseMaterial.objects.create(
            course=course,
            file=SimpleUploadedFile("lesson1.pdf", b"pdf-content"),
            uploaded_by=teacher,
        )
        self.client.force_login(teacher)

        response = self.client.post(reverse("courses:material_delete", args=[course.id, material.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CourseMaterial.objects.filter(id=material.id).exists())


class CourseDeadlineTests(CoursesBaseTestCase):
    def test_teacher_can_add_edit_and_delete_deadline(self):
        teacher = self.create_teacher()
        course = self.create_course(teacher=teacher, course_id="DL101")
        self.client.force_login(teacher)

        add_response = self.client.post(
            reverse("courses:deadline_add", args=[course.id]),
            data={
                "title": "Assignment 1",
                "description": "First assignment",
                "due_at": "2030-01-10T10:30",
            },
        )

        self.assertEqual(add_response.status_code, 302)
        deadline = Deadline.objects.get(course=course, title="Assignment 1")
        self.assertEqual(deadline.description, "First assignment")

        edit_response = self.client.post(
            reverse("courses:deadline_edit", args=[course.id, deadline.id]),
            data={
                "title": "Assignment 1 Updated",
                "description": "Updated description",
                "due_at": "2030-01-11T11:45",
            },
        )

        self.assertEqual(edit_response.status_code, 302)
        deadline.refresh_from_db()
        self.assertEqual(deadline.title, "Assignment 1 Updated")
        self.assertEqual(deadline.description, "Updated description")

        delete_response = self.client.post(reverse("courses:deadline_delete", args=[course.id, deadline.id]))

        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Deadline.objects.filter(id=deadline.id).exists())

    def test_non_teacher_cannot_add_deadline(self):
        teacher = self.create_teacher()
        student = self.create_user()
        course = self.create_course(teacher=teacher, course_id="DL102")
        self.client.force_login(student)

        response = self.client.post(
            reverse("courses:deadline_add", args=[course.id]),
            data={"title": "Blocked", "due_at": "2030-01-10T10:30"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Deadline.objects.filter(course=course).count(), 0)
