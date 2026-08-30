from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeView,
)
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods


from .forms import (
    LoginForm,
    RegisterForm,
    UserProfileForm,
    UserSettingsForm,
    UserUpdateForm,
)
from .models import UserProfile


@require_http_methods(["GET", "POST"])
def register_view(request):
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


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)

        remember_me = form.cleaned_data.get(
            "remember_me",
            False,
        )

        if remember_me:
            self.request.session.set_expiry(
                60 * 60 * 24 * 14,
            )
        else:
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
        messages.error(
            self.request,
            "Invalid username or password.",
        )

        return super().form_invalid(form)

    def get_success_url(self):
        return (
            self.get_redirect_url()
            or reverse_lazy("dashboard:dashboard")
        )


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("accounts:login")


@login_required
@require_http_methods(["GET"])
def profile_view(request):
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


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_view(request):
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


@login_required
@require_http_methods(["GET", "POST"])
def settings_view(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        form = UserSettingsForm(
            request.POST,
            instance=profile,
        )

        if form.is_valid():
            saved_profile = form.save()

            request.session["expense_tracker_theme"] = (
                saved_profile.theme
            )

            messages.success(
                request,
                "Your settings have been saved successfully.",
            )

            return redirect("accounts:settings")

        messages.error(
            request,
            "Please correct the settings below.",
        )
    else:
        form = UserSettingsForm(
            instance=profile,
        )

    return render(
        request,
        "accounts/settings.html",
        {
            "form": form,
            "profile": profile,
        },
    )


class CustomPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Your password has been changed successfully.",
        )

        return super().form_valid(form)