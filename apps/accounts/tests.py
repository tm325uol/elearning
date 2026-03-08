from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.accounts.forms import SignupForm
from apps.courses.models import Course, Teaching, Enrollment

User = get_user_model()


class AccountsBaseTestCase(TestCase):
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


class UserModelTests(AccountsBaseTestCase):
    def test_str_representation(self):
        user = self.create_user()
        self.assertEqual(str(user), "Student One (@student1)")

    def test_short_name_returns_first_name_segment(self):
        user = self.create_user(full_name="Alice Bob Carol")
        self.assertEqual(user.short_name, "Alice")

    def test_avatar_url_falls_back_to_ui_avatar_service(self):
        user = self.create_user(full_name="Alice Bob")
        self.assertIn("ui-avatars.com", user.avatar_url)
        self.assertIn("Alice+Bob", user.avatar_url)

    def test_role_helpers(self):
        student = self.create_user()
        teacher = self.create_teacher()
        self.assertTrue(student.is_student)
        self.assertFalse(student.is_teacher)
        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_student)


class SignupFormTests(AccountsBaseTestCase):
    def test_signup_form_creates_user_with_hashed_password_and_full_name(self):
        form = SignupForm(
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "role": User.Role.STUDENT,
                "fullname": "New User",
                "password": "SafePassword123!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.full_name, "New User")
        self.assertNotEqual(user.password, "SafePassword123!")
        self.assertTrue(user.check_password("SafePassword123!"))

    def test_signup_form_rejects_duplicate_email(self):
        self.create_user(email="taken@example.com")
        form = SignupForm(
            data={
                "username": "anotheruser",
                "email": "taken@example.com",
                "role": User.Role.STUDENT,
                "fullname": "Another User",
                "password": "SafePassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_signup_form_rejects_duplicate_username(self):
        self.create_user(username="takenusername")
        form = SignupForm(
            data={
                "username": "takenusername",
                "email": "unique@example.com",
                "role": User.Role.STUDENT,
                "fullname": "Another User",
                "password": "SafePassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


class AuthenticationViewTests(AccountsBaseTestCase):
    def test_signup_page_renders_for_guests(self):
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account")

    def test_signup_post_creates_user_and_logs_them_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            data={
                "username": "signupuser",
                "email": "signupuser@example.com",
                "role": User.Role.STUDENT,
                "fullname": "Signup User",
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))
        self.assertTrue(User.objects.filter(username="signupuser").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_signup_redirects_authenticated_users_away(self):
        user = self.create_user()
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:signup"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_login_with_valid_credentials_redirects_to_home(self):
        self.create_user(username="loginuser", password="ValidPass123!")

        response = self.client.post(
            reverse("accounts:login"),
            data={"username": "loginuser", "password": "ValidPass123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_respects_safe_next_parameter(self):
        self.create_user(username="loginuser", password="ValidPass123!")

        response = self.client.post(
            f'{reverse("accounts:login")}?next=/@loginuser/',
            data={"username": "loginuser", "password": "ValidPass123!"},
        )

        self.assertRedirects(response, "/@loginuser/")

    def test_login_rejects_unsafe_next_parameter(self):
        self.create_user(username="loginuser", password="ValidPass123!")

        response = self.client.post(
            f'{reverse("accounts:login")}?next=https://evil.example.com/',
            data={"username": "loginuser", "password": "ValidPass123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:home"))

    def test_login_with_invalid_credentials_shows_error(self):
        self.create_user(username="loginuser", password="ValidPass123!")

        response = self.client.post(
            reverse("accounts:login"),
            data={"username": "loginuser", "password": "WrongPass"},
            follow=True,
        )

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Invalid username or password.", messages)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        user = self.create_user()
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_via_post_clears_session_and_redirects(self):
        user = self.create_user()
        self.client.force_login(user)

        response = self.client.post(reverse("accounts:logout"), follow=True)

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("You have been successfully logged out.", messages)


class ProfileViewTests(AccountsBaseTestCase):
    def test_dashboard_redirect_requires_login(self):
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_dashboard_redirect_sends_logged_in_user_to_their_profile(self):
        user = self.create_user(username="myuser")
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:home"))
        self.assertRedirects(response, reverse("accounts:user_profile", kwargs={"username": "myuser"}))

    def test_teacher_profile_is_public(self):
        teacher = self.create_teacher(username="teacherpublic")

        response = self.client.get(reverse("accounts:user_profile", kwargs={"username": teacher.username}))
        self.assertEqual(response.status_code, 200)

    def test_student_profile_redirects_guest_to_login(self):
        student = self.create_user(username="studentprivate")

        response = self.client.get(reverse("accounts:user_profile", kwargs={"username": student.username}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertIn(f"next=/@{student.username}/", response.url)

    def test_logged_in_user_can_view_student_profile(self):
        visitor = self.create_teacher(username="visitor")
        student = self.create_user(username="studentprivate")
        self.client.force_login(visitor)

        response = self.client.get(reverse("accounts:user_profile", kwargs={"username": student.username}))
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_updates_text_fields(self):
        user = self.create_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:edit_profile"),
            data={
                "full_name": "Updated Name",
                "location": "Ho Chi Minh City",
                "bio": "Updated bio",
                "next": reverse("accounts:user_profile", kwargs={"username": user.username}),
            },
        )

        self.assertRedirects(response, reverse("accounts:user_profile", kwargs={"username": user.username}))
        user.refresh_from_db()
        self.assertEqual(user.full_name, "Updated Name")
        self.assertEqual(user.location, "Ho Chi Minh City")
        self.assertEqual(user.bio, "Updated bio")

    def test_edit_profile_can_remove_existing_photo(self):
        user = self.create_user()
        user.profile_photo = SimpleUploadedFile("avatar.jpg", b"filecontent", content_type="image/jpeg")
        user.save()
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:edit_profile"),
            data={"remove_photo": "1"},
        )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(bool(user.profile_photo))


class AccountsApiTests(AccountsBaseTestCase):
    def test_user_search_requires_login(self):
        response = self.client.get(reverse("api:accounts_api:search"))
        self.assertEqual(response.status_code, 403)

    def test_user_search_filters_by_query_and_role(self):
        requester = self.create_user(username="requester")
        self.create_teacher(username="teacheralpha", full_name="Alice Teacher", email="alice@example.com")
        self.create_user(username="studentbeta", full_name="Bob Student", email="bob@example.com")
        self.client.force_login(requester)

        response = self.client.get(
            reverse("api:accounts_api:search"),
            data={"q": "alice", "role": "teacher"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["username"], "teacheralpha")
        self.assertEqual(payload["results"][0]["role"], "Teacher")

    def test_user_search_returns_only_active_users(self):
        requester = self.create_user(username="requester")
        self.create_user(username="activeuser", full_name="Active User", email="active@example.com", is_active=True)
        self.create_user(username="inactiveuser", full_name="Inactive User", email="inactive@example.com", is_active=False)
        self.client.force_login(requester)

        response = self.client.get(reverse("api:accounts_api:search"), data={"q": "user"})

        usernames = [result["username"] for result in response.json()["results"]]
        self.assertIn("activeuser", usernames)
        self.assertNotIn("inactiveuser", usernames)

    def test_user_search_limits_results_to_15(self):
        requester = self.create_user(username="requester")
        self.client.force_login(requester)

        for i in range(20):
            self.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
            )

        response = self.client.get(reverse("api:accounts_api:search"))
        self.assertEqual(len(response.json()["results"]), 15)

    def test_user_profile_api_requires_login(self):
        user = self.create_user(username="apiuser")
        response = self.client.get(reverse("api:accounts_api:detail", kwargs={"username": user.username}))
        self.assertEqual(response.status_code, 403)

    def test_user_profile_api_returns_expected_payload_for_teacher(self):
        requester = self.create_user(username="requester")
        teacher = self.create_teacher(username="teacherapi", full_name="Teacher Api")
        course = Course.objects.create(course_id="CS101", title="Intro Course")
        Teaching.objects.create(teacher=teacher, course=course)
        self.client.force_login(requester)

        response = self.client.get(reverse("api:accounts_api:detail", kwargs={"username": teacher.username}))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["username"], "teacherapi")
        self.assertEqual(payload["role"], "Teacher")
        self.assertEqual(payload["teaching_courses"][0]["title"], "Intro Course")
        self.assertIsNone(payload["enrolled_courses"])

    def test_user_profile_api_returns_expected_payload_for_student(self):
        requester = self.create_teacher(username="requester")
        student = self.create_user(username="studentapi", full_name="Student Api")
        course = Course.objects.create(course_id="CS102", title="Data Structures")
        Enrollment.objects.create(student=student, course=course)
        self.client.force_login(requester)

        response = self.client.get(reverse("api:accounts_api:detail", kwargs={"username": student.username}))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["username"], "studentapi")
        self.assertEqual(payload["role"], "Student")
        self.assertEqual(payload["enrolled_courses"], 1)
        self.assertIsNone(payload["teaching_courses"])
