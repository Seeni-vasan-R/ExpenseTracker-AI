from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import (
    RegisterForm,
    LoginForm,
    UserUpdateForm,
    UserProfileForm,
)
from .models import UserProfile


# =========================
# REGISTER
# =========================

def register_view(request):

    # If already logged in, go to main dashboard
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                f"Account created successfully for {user.username}. "
                "You can now log in."
            )

            return redirect("accounts:login")

        messages.error(
            request,
            "Please correct the errors below."
        )

    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


# =========================
# LOGIN
# =========================

class CustomLoginView(LoginView):

    template_name = "accounts/login.html"

    authentication_form = LoginForm

    redirect_authenticated_user = True

    def form_valid(self, form):

        remember_me = form.cleaned_data.get("remember_me")

        # Login user
        response = super().form_valid(form)

        # Remember-me session
        if remember_me:

            # 2 weeks
            self.request.session.set_expiry(1209600)

        else:

            # Session expires when browser closes
            self.request.session.set_expiry(0)

        messages.success(
            self.request,
            f"Welcome back, "
            f"{self.request.user.first_name or self.request.user.username}!"
        )

        return response

    def form_invalid(self, form):

        messages.error(
            self.request,
            "Invalid username or password."
        )

        return super().form_invalid(form)

    def get_success_url(self):

        # AFTER LOGIN → MAIN DASHBOARD
        return reverse_lazy("dashboard:dashboard")


# =========================
# LOGOUT
# =========================

@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("accounts:login")


# =========================
# PROFILE
# =========================

@login_required
def profile_view(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "user_obj": request.user,
            "profile": profile,
        }
    )


# =========================
# EDIT PROFILE
# =========================

@login_required
def edit_profile_view(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        user_form = UserUpdateForm(
            request.POST,
            instance=request.user
        )

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()
            profile_form.save()

            messages.success(
                request,
                "Your profile has been updated successfully."
            )

            return redirect("accounts:profile")

        messages.error(
            request,
            "Please correct the errors below."
        )

    else:

        user_form = UserUpdateForm(
            instance=request.user
        )

        profile_form = UserProfileForm(
            instance=profile
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        }
    )
