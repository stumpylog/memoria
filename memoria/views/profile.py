import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from memoria.forms import UserEmailForm
from memoria.forms import UserProfileUpdateForm
from memoria.models import UserProfile

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

        # Instantiate forms with initial data for display
        email_form = UserEmailForm(instance=user)
        profile_form = UserProfileUpdateForm(instance=profile)

        user_groups = user.groups.all()

        # Get all groups to display for staff users
        all_groups = Group.objects.all() if user.is_staff else None

        context.update(
            {
                "title": "Your Profile",
                "user": user,
                "email_form": email_form,
                "profile_form": profile_form,
                "user_groups": user_groups,
                "all_groups": all_groups,  # Pass None if not staff
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
            # Note: Form errors won't be directly displayed on the redirected page
            # via messages. A general error message is added.
            messages.error(request, "Failed to update email. Please correct the errors.")

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
            # Note: Form errors won't be directly displayed on the redirected page.
            messages.error(request, "Failed to update profile details. Please correct the errors.")

        return redirect("profile")  # Redirect back to the main profile view


class ManageGroupsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Handles POST requests to manage user group memberships (staff only).
    """

    def test_func(self) -> bool:
        """
        Only allow staff users to access this view.
        """
        return self.request.user.is_staff

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseRedirect:  # noqa: ARG002
        user: User = request.user

        user_to_manage: User = user

        selected_group_ids_str: list[str] = request.POST.getlist("groups")
        selected_group_ids: list[int] = []
        for group_id_str in selected_group_ids_str:
            try:
                selected_group_ids.append(int(group_id_str))
            except ValueError:  # noqa: PERF203
                messages.error(request, f"Invalid group ID received: {group_id_str}")
                return redirect("profile")  # Redirect on error

        try:
            selected_groups = Group.objects.filter(pk__in=selected_group_ids)
            user_to_manage.groups.set(selected_groups)
            messages.success(request, f"Group memberships for {user_to_manage.username} successfully updated!")

        except Exception as e:  # noqa: BLE001
            messages.error(request, f"An error occurred while updating group memberships: {e}")

        return redirect("profile")  # Redirect back to the main profile view
