from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from .forms import (
    LoginForm,
    RegisterForm,
    UserProfileForm,
    UserUpdateForm,
)
from .models import UserProfile


# -----------------------------------------------------------------------------
# Register
# -----------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Register a new user account and create the user's profile.
    """
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = form.save()

                UserProfile.objects.get_or_create(
                    user=user,
                )

            messages.success(
                request,
                (
                    f"Account created successfully for {user.username}. "
                    "You can now log in."
                ),
            )

            return redirect("accounts:login")

        messages.error(
            request,
            "Please correct the errors below.",
        )
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


# -----------------------------------------------------------------------------
# Login
# -----------------------------------------------------------------------------

class CustomLoginView(LoginView):
    """
    Login view with username/email support and remember-me handling.
    """

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        """
        Authenticate the user and configure the session lifetime.
        """
        response = super().form_valid(form)

        remember_me = form.cleaned_data.get(
            "remember_me",
            False,
        )

        if remember_me:
            # Keep the session active for 14 days.
            self.request.session.set_expiry(
                60 * 60 * 24 * 14,
            )
        else:
            # Expire the session when the browser closes.
            self.request.session.set_expiry(0)

        display_name = (
            self.request.user.first_name
            or self.request.user.username
        )

        messages.success(
            self.request,
            f"Welcome back, {display_name}!",
        )

        return response

    def form_invalid(self, form):
        """
        Display a generic login error.
        """
        messages.error(
            self.request,
            "Invalid username or password.",
        )

        return super().form_invalid(form)

    def get_success_url(self):
        """
        Respect the ?next= parameter when present. Otherwise, send the user
        to the dashboard.
        """
        return (
            self.get_redirect_url()
            or reverse_lazy("dashboard:dashboard")
        )


# -----------------------------------------------------------------------------
# Logout
# -----------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """
    Log out the current user.

    Logout is restricted to POST to avoid changing authentication state through
    a simple GET link.
    """
    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("accounts:login")


# -----------------------------------------------------------------------------
# Profile
# -----------------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def profile_view(request):
    """
    Display the authenticated user's profile.
    """
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "user_obj": request.user,
            "profile": profile,
        },
    )


# -----------------------------------------------------------------------------
# Edit profile
# -----------------------------------------------------------------------------

@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_view(request):
    """
    Update the authenticated user's account and profile information.
    """
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        user_form = UserUpdateForm(
            request.POST,
            instance=request.user,
        )

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect("accounts:profile")

        messages.error(
            request,
            "Please correct the errors below.",
        )
    else:
        user_form = UserUpdateForm(
            instance=request.user,
        )

        profile_form = UserProfileForm(
            instance=profile,
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )