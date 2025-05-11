import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from memoria.forms import GroupMembershipForm
from memoria.forms import UserEmailForm
from memoria.forms import UserProfileUpdateForm
from memoria.models import UserProfile
from memoria.views.mixins import StaffOrSuperuserRequiredMixin

User = get_user_model()

logger = logging.getLogger(__name__)


def get_or_create_user_profile(user: User) -> UserProfile:
    """
    Helper function to get or create a UserProfile for a given user.
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Displays the user's profile and forms for editing using TemplateView.
    """

    template_name: str = "profile.html.jinja"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Provides context data for the template."""
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        profile: UserProfile = get_or_create_user_profile(user)

        # Check if email form data/errors are in the session (from a failed POST)
        email_form_session_data = self.request.session.pop("profile_email_form_data", None)
        if email_form_session_data:
            # Reconstruct the form with the data from the session
            email_form = UserEmailForm(email_form_session_data, instance=user)
            # The form.is_valid() check might be needed here if errors weren't stored explicitly
            # but instantiating with data usually regenerates errors on access if validation failed.
            # For simplicity, we rely on Django forms regenerating errors when template accesses .errors
        else:
            # Instantiate with the current user instance data
            email_form = UserEmailForm(instance=user)

        profile_form_session_data = self.request.session.pop("profile_details_form_data", None)
        if profile_form_session_data:
            # Reconstruct the form with the data from the session
            profile_form = UserProfileUpdateForm(profile_form_session_data, instance=profile)
        else:
            # Instantiate with the current profile instance data
            profile_form = UserProfileUpdateForm(instance=profile)

        if user.is_staff or user.is_superuser:
            group_form_session_data = self.request.session.pop("profile_group_form_data", None)
            if group_form_session_data:
                # Pass the user instance to set initial values correctly
                group_form: GroupMembershipForm = GroupMembershipForm(group_form_session_data, user=user)
            else:
                # Pass the user instance to set initial values correctly
                group_form: GroupMembershipForm = GroupMembershipForm(user=user)
        else:
            group_form = None

        user_groups = user.groups.all()

        context.update(
            {
                "title": "Your Profile",
                "user": user,
                "email_form": email_form,
                "profile_form": profile_form,
                "group_form": group_form,
                "user_groups": user_groups,
            },
        )
        return context


class UpdateEmailView(LoginRequiredMixin, View):
    """
    Handles POST requests to update the user's email address.
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseRedirect:  # noqa: ARG002
        user: User = request.user
        email_form = UserEmailForm(request.POST, instance=user)

        if email_form.is_valid():
            email_form.save()
            messages.success(request, "Your email address was successfully updated!")
        else:
            request.session["profile_email_form_data"] = request.POST  # Store raw POST data
            messages.error(request, "Please correct the errors below.")  # Generic error message

        return redirect("profile")  # Redirect back to the main profile view


class UpdateProfileView(LoginRequiredMixin, View):
    """
    Handles POST requests to update user profile details (bio, images per page).
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseRedirect:  # noqa: ARG002
        user: User = request.user
        profile: UserProfile = get_or_create_user_profile(user)
        profile_form = UserProfileUpdateForm(request.POST, instance=profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile details were successfully updated!")
        else:
            # If invalid, store form data in session and add an error message
            request.session["profile_details_form_data"] = request.POST  # Store raw POST data
            messages.error(request, "Please correct the errors below.")  # Generic error message

        return redirect("profile")  # Redirect back to the main profile view


class ManageGroupsView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, View):
    """
    Handles POST requests to manage user group memberships (staff only).
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseRedirect:  # noqa: ARG002
        user: User = request.user  # The user making the request (staff)
        user_to_manage: User = user  # Assuming staff manages their own groups for now

        # Instantiate the form with POST data and the user instance
        group_form = GroupMembershipForm(request.POST, user=user_to_manage)

        if group_form.is_valid():
            # Get the list of selected group objects from the cleaned data
            selected_groups = group_form.cleaned_data["groups"]

            try:
                # Update the user's groups using the set method
                user_to_manage.groups.set(selected_groups)
                messages.success(request, f"Group memberships for {user_to_manage.username} successfully updated!")

            except Exception as e:  # noqa: BLE001
                messages.error(request, f"An unexpected error occurred while updating group memberships: {e}")

        else:
            # If the form is invalid (e.g., invalid group ID somehow), store data in session
            request.session["profile_group_form_data"] = request.POST  # Store raw POST data
            messages.error(request, "Please correct the errors below for group management.")  # Generic error

        return redirect("profile")  # Always redirect back to the main profile view


def login_view(request: HttpRequest):
    pass


def logout_view(request: HttpRequest):
    pass
