from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

from PIL import Image

from .models import UserProfile


User = get_user_model()


def dashboard_test_view(request):
    """
    Minimal dashboard view used only for URL reversing during tests.
    """
    return HttpResponse("Dashboard")


dashboard_test_urlpatterns = (
    [
        path(
            "",
            dashboard_test_view,
            name="dashboard",
        ),
    ],
    "dashboard",
)


urlpatterns = [
    path(
        "accounts/",
        include("accounts.urls"),
    ),
    path(
        "dashboard/",
        include(
            dashboard_test_urlpatterns,
            namespace="dashboard",
        ),
    ),
]


def create_test_image(
    filename: str = "profile.png",
    image_format: str = "PNG",
) -> SimpleUploadedFile:
    """
    Create a small valid image for upload tests.
    """
    image = Image.new(
        "RGB",
        (100, 100),
        color="blue",
    )

    image_buffer = BytesIO()
    image.save(
        image_buffer,
        format=image_format,
    )
    image_buffer.seek(0)

    content_type = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }[image_format]

    return SimpleUploadedFile(
        name=filename,
        content=image_buffer.read(),
        content_type=content_type,
    )


class AccountsTestCase(TestCase):
    """
    Base test case containing shared account test data.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
            first_name="Test",
            last_name="User",
        )


@override_settings(ROOT_URLCONF="accounts.tests")
class RegisterViewTests(AccountsTestCase):
    """
    Tests for user registration.
    """

    def test_register_page_is_accessible(self):
        response = self.client.get(
            reverse("accounts:register"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/register.html",
        )

    def test_successful_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            data={
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@example.com",
                "password1": "AnotherStrongPassword123!",
                "password2": "AnotherStrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("accounts:login"),
        )

        new_user = User.objects.get(
            username="newuser",
        )

        self.assertEqual(
            new_user.email,
            "newuser@example.com",
        )
        self.assertEqual(
            new_user.first_name,
            "New",
        )
        self.assertEqual(
            new_user.last_name,
            "User",
        )
        self.assertTrue(
            new_user.check_password(
                "AnotherStrongPassword123!",
            )
        )
        self.assertTrue(
            UserProfile.objects.filter(
                user=new_user,
            ).exists()
        )

    def test_registration_normalizes_email_and_username_whitespace(self):
        response = self.client.post(
            reverse("accounts:register"),
            data={
                "username": "  newuser  ",
                "first_name": " New ",
                "last_name": " User ",
                "email": "  NEWUSER@EXAMPLE.COM  ",
                "password1": "AnotherStrongPassword123!",
                "password2": "AnotherStrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)

        new_user = User.objects.get(
            username="newuser",
        )

        self.assertEqual(
            new_user.email,
            "newuser@example.com",
        )
        self.assertEqual(
            new_user.first_name,
            "New",
        )
        self.assertEqual(
            new_user.last_name,
            "User",
        )

    def test_duplicate_username_is_rejected_case_insensitively(self):
        response = self.client.post(
            reverse("accounts:register"),
            data={
                "username": "TESTUSER",
                "first_name": "Another",
                "last_name": "User",
                "email": "another@example.com",
                "password1": "AnotherStrongPassword123!",
                "password2": "AnotherStrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "already taken",
        )

    def test_duplicate_email_is_rejected_case_insensitively(self):
        response = self.client.post(
            reverse("accounts:register"),
            data={
                "username": "anotheruser",
                "first_name": "Another",
                "last_name": "User",
                "email": "TEST@EXAMPLE.COM",
                "password1": "AnotherStrongPassword123!",
                "password2": "AnotherStrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "email already exists",
        )

    def test_invalid_password_confirmation_is_rejected(self):
        response = self.client.post(
            reverse("accounts:register"),
            data={
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@example.com",
                "password1": "AnotherStrongPassword123!",
                "password2": "DifferentPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(
                username="newuser",
            ).exists()
        )

    def test_authenticated_user_is_redirected_to_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:register"),
        )

        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
        )


@override_settings(ROOT_URLCONF="accounts.tests")
class LoginViewTests(AccountsTestCase):
    """
    Tests for login using username and email.
    """

    def test_login_page_is_accessible(self):
        response = self.client.get(
            reverse("accounts:login"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/login.html",
        )

    def test_login_with_username_succeeds(self):
        response = self.client.post(
            reverse("accounts:login"),
            data={
                "username": "testuser",
                "password": "StrongPassword123!",
                "remember_me": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
        )
        self.assertEqual(
            int(self.client.session.get_expiry_age()),
            60 * 60 * 24 * 14,
        )

    def test_login_with_email_succeeds(self):
        response = self.client.post(
            reverse("accounts:login"),
            data={
                "username": "TEST@EXAMPLE.COM",
                "password": "StrongPassword123!",
                "remember_me": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
        )
        self.assertTrue(
            response.wsgi_request.user.is_authenticated,
        )

    def test_login_without_remember_me_expires_on_browser_close(self):
        response = self.client.post(
            reverse("accounts:login"),
            data={
                "username": "testuser",
                "password": "StrongPassword123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
        )
        self.assertEqual(
            int(self.client.session.get_expiry_age()),
            0,
        )

    def test_invalid_login_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            data={
                "username": "testuser",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated,
        )
        self.assertContains(
            response,
            "Invalid username or password",
        )

    def test_login_respects_next_parameter(self):
        response = self.client.post(
            f"{reverse('accounts:login')}?next=/private-page/",
            data={
                "username": "testuser",
                "password": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/private-page/",
        )


@override_settings(ROOT_URLCONF="accounts.tests")
class LogoutViewTests(AccountsTestCase):
    """
    Tests for user logout.
    """

    def test_authenticated_user_can_logout_with_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:logout"),
        )

        self.assertRedirects(
            response,
            reverse("accounts:login"),
        )
        self.assertFalse(
            response.wsgi_request.user.is_authenticated,
        )

    def test_logout_get_request_is_not_allowed(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:logout"),
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated,
        )


@override_settings(ROOT_URLCONF="accounts.tests")
class ProfileViewTests(AccountsTestCase):
    """
    Tests for viewing and editing profiles.
    """

    def test_anonymous_user_is_redirected_from_profile(self):
        response = self.client.get(
            reverse("accounts:profile"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("accounts:login"),
            response.url,
        )

    def test_profile_page_creates_missing_profile(self):
        self.client.force_login(self.user)

        UserProfile.objects.filter(
            user=self.user,
        ).delete()

        response = self.client.get(
            reverse("accounts:profile"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/profile.html",
        )
        self.assertTrue(
            UserProfile.objects.filter(
                user=self.user,
            ).exists()
        )

    def test_profile_page_is_accessible_to_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:profile"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "testuser",
        )

    def test_edit_profile_page_is_accessible(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:edit_profile"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/edit_profile.html",
        )

    def test_user_profile_can_be_updated(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:edit_profile"),
            data={
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@example.com",
                "phone_number": "+919876543210",
                "country": "India",
                "currency": "INR",
                "theme": "dark",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Updated",
        )
        self.assertEqual(
            self.user.last_name,
            "Name",
        )
        self.assertEqual(
            self.user.email,
            "updated@example.com",
        )

        profile = UserProfile.objects.get(
            user=self.user,
        )

        self.assertEqual(
            profile.phone_number,
            "+919876543210",
        )
        self.assertEqual(
            profile.country,
            "India",
        )
        self.assertEqual(
            profile.currency,
            "INR",
        )
        self.assertEqual(
            profile.theme,
            "dark",
        )

    def test_profile_picture_can_be_uploaded(self):
        self.client.force_login(self.user)

        profile_picture = create_test_image()

        response = self.client.post(
            reverse("accounts:edit_profile"),
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "phone_number": "+919876543210",
                "country": "India",
                "currency": "INR",
                "theme": "light",
                "profile_picture": profile_picture,
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

        profile = UserProfile.objects.get(
            user=self.user,
        )

        self.assertTrue(
            profile.profile_picture,
        )

    def test_duplicate_profile_email_is_rejected(self):
        second_user = User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="StrongPassword123!",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:edit_profile"),
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": second_user.email,
                "phone_number": "+919876543210",
                "country": "India",
                "currency": "INR",
                "theme": "light",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "email already exists",
        )


class UserProfileSignalTests(TestCase):
    """
    Tests for automatic profile creation through accounts.signals.
    """

    def test_profile_is_created_when_user_is_created(self):
        user = User.objects.create_user(
            username="signaluser",
            email="signal@example.com",
            password="StrongPassword123!",
        )

        self.assertTrue(
            UserProfile.objects.filter(
                user=user,
            ).exists()
        )