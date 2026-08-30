from typing import TYPE_CHECKING, Any

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from PIL import Image, UnidentifiedImageError

from .models import UserProfile


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
                "autocomplete": "email",
            }
        ),
    )

    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First name",
                "autocomplete": "given-name",
            }
        ),
    )

    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last name",
                "autocomplete": "family-name",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Username",
                "autocomplete": "username",
            }
        )

        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "new-password",
            }
        )

        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirm password",
                "autocomplete": "new-password",
            }
        )

    def clean_email(self) -> str:
        email = (
            self.cleaned_data.get("email") or ""
        ).strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_username(self) -> str:
        username = (
            self.cleaned_data.get("username") or ""
        ).strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():
            raise ValidationError(
                "This username is already taken."
            )

        return username

    def clean_first_name(self) -> str:
        first_name = (
            self.cleaned_data.get("first_name") or ""
        ).strip()

        if not first_name:
            raise ValidationError(
                "First name is required."
            )

        return first_name

    def clean_last_name(self) -> str:
        last_name = (
            self.cleaned_data.get("last_name") or ""
        ).strip()

        if not last_name:
            raise ValidationError(
                "Last name is required."
            )

        return last_name

    def save(
        self,
        commit: bool = True,
    ) -> "AbstractUser":
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()

        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username or email",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        ),
    )

    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    def clean(self) -> dict[str, Any]:
        username_value = self.cleaned_data.get("username")

        if username_value:
            identifier = username_value.strip()

            user = (
                User.objects
                .filter(username__iexact=identifier)
                .first()
            )

            if user is None:
                email_matches = User.objects.filter(
                    email__iexact=identifier
                )

                if email_matches.count() == 1:
                    user = email_matches.first()

                elif email_matches.count() > 1:
                    raise ValidationError(
                        "Multiple accounts use this email address. "
                        "Please log in with your username."
                    )

            if user is not None:
                self.cleaned_data["username"] = (
                    user.get_username()
                )

        return super().clean()


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "family-name",
                }
            ),
        }

    def clean_first_name(self) -> str:
        return (
            self.cleaned_data.get("first_name") or ""
        ).strip()

    def clean_last_name(self) -> str:
        return (
            self.cleaned_data.get("last_name") or ""
        ).strip()

    def clean_email(self) -> str:
        email = (
            self.cleaned_data.get("email") or ""
        ).strip().lower()

        queryset = (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
        )

        if queryset.exists():
            raise ValidationError(
                "An account with this email already exists."
            )

        return email


class UserProfileForm(forms.ModelForm):
    """
    Form for personal profile information only.

    Currency and theme are intentionally managed by
    UserSettingsForm on the Settings page.
    """

    class Meta:
        model = UserProfile
        fields = [
            "profile_picture",
            "phone_number",
            "country",
        ]
        widgets = {
            "profile_picture": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+919999999999",
                    "autocomplete": "tel",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Country",
                    "autocomplete": "country-name",
                }
            ),
        }

    def clean_phone_number(self) -> str:
        return (
            self.cleaned_data.get("phone_number") or ""
        ).strip()

    def clean_country(self) -> str:
        return (
            self.cleaned_data.get("country") or ""
        ).strip()

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")

        if not picture:
            return picture

        if not isinstance(picture, UploadedFile):
            return picture

        if picture.size > 2 * 1024 * 1024:
            raise ValidationError(
                "Image size must not exceed 2 MB."
            )

        allowed_formats = {
            "JPEG",
            "PNG",
            "WEBP",
        }

        image_format = None

        try:
            picture.seek(0)

            with Image.open(picture) as image:
                image.verify()
                image_format = image.format

        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
        ) as error:
            raise ValidationError(
                "Upload a valid JPEG, PNG, or WEBP image."
            ) from error

        finally:
            picture.seek(0)

        if image_format not in allowed_formats:
            raise ValidationError(
                "Only JPEG, PNG, or WEBP images are allowed."
            )

        return picture


class UserSettingsForm(forms.ModelForm):
    """
    Form for application preferences only.
    """

    class Meta:
        model = UserProfile
        fields = [
            "currency",
            "theme",
        ]
        widgets = {
            "currency": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "theme": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "settings-theme-select",
                }
            ),
        }