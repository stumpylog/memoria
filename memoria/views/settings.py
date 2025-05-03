import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic import View

from memoria.forms import AddGroupForm
from memoria.forms import AddUserForm
from memoria.forms import ManageUserGroupsForm
from memoria.views.mixins import StaffOrSuperuserRequiredMixin

User = get_user_model()
logger = logging.getLogger(__name__)


class AdminSettingsView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, TemplateView):
    """
    Displays the main admin settings page with tabs for managing users and groups.
    Provides forms for adding users and groups, handling forms data/errors from session.
    """

    template_name = "settings/view.html.jinja"

    def get_context_data(self, **kwargs):
        """
        Adds lists of users and groups, and forms for adding them to the context.
        Handles loading form data and errors from the session if available (PRG pattern).
        """
        context = super().get_context_data(**kwargs)

        add_user_form_data = self.request.session.pop("add_user_form_data", None)

        add_user_form = AddUserForm(add_user_form_data) if add_user_form_data else AddUserForm()

        # --- Handle Add Group Form from Session (PRG) ---
        add_group_form_data = self.request.session.pop("add_group_form_data", None)

        add_group_form = AddGroupForm(add_group_form_data) if add_group_form_data else AddGroupForm()

        context["title"] = "Admin Settings"
        context["users"] = User.objects.all().order_by("username")
        context["groups"] = Group.objects.all().order_by("name")
        context["add_user_form"] = add_user_form
        context["add_group_form"] = add_group_form

        return context


class AddUserView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, View):
    """
    Handles the creation of a new user via a POST request using PRG pattern.
    Stores form data and errors in session on failure.
    """

    def post(self, request: HttpRequest, *args, **kwargs):  # noqa: ARG002
        add_user_form = AddUserForm(request.POST)
        if add_user_form.is_valid():
            add_user_form.save()
            messages.success(request, f"User '{add_user_form.cleaned_data['username']}' created successfully.")
            # Redirect on success - no need to store form data/errors
            return redirect(reverse("settings") + "#manage-users")
        # Form is invalid - store data and errors in session
        request.session["add_user_form_data"] = request.POST
        messages.error(request, "Error creating user. Please check the form.")  # Generic error message
        # Redirect to the GET view
        return redirect(reverse("settings") + "#manage-users")


class ToggleUserActiveView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, View):
    """
    Handles toggling the is_active status of a user via a POST request.
    """

    def post(self, request: HttpRequest, pk: int, *args, **kwargs):  # noqa: ARG002
        user = get_object_or_404(User, pk=pk)

        if user.pk == self.request.user.pk:
            messages.error(request, "You cannot deactivate your own account.")
            # Redirect back to the settings page without making changes
            return redirect(reverse("settings") + "#manage-users")

        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User '{user.username}' has been {status}.")
        # Redirect after action
        return redirect(reverse("settings") + "#manage-users")


class ManageUserGroupsView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, TemplateView):
    """
    View for managing a specific user's group memberships.
    Displays current groups and a form to update memberships.
    """

    template_name = "settings/manage_user_groups.html.jinja"

    def get_context_data(self, pk: int, **kwargs):
        """
        Adds the target user, all groups, and the group management form to the context.
        Handles loading form data and errors from the session if available (PRG pattern).
        """
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, pk=pk)
        context["title"] = f"Manage Groups for {user.username}"
        context["target_user"] = user

        # --- Handle Manage User Groups Form from Session (PRG) ---
        manage_groups_form_data = self.request.session.pop("manage_user_groups_form_data", None)

        if manage_groups_form_data:
            # Instantiate form with data and errors from session and the user instance
            manage_groups_form = ManageUserGroupsForm(manage_groups_form_data, instance=user)
        else:
            # No data in session, provide a new unbound form for the user instance
            manage_groups_form = ManageUserGroupsForm(instance=user)

        context["manage_groups_form"] = manage_groups_form

        return context

    def post(self, request: HttpRequest, pk: int, *args, **kwargs):  # noqa: ARG002
        """
        Handles updating the group memberships for the target user via a POST request.
        Implements PRG pattern for form submission.
        """
        user = get_object_or_404(User, pk=pk)
        logger.info(f"Pk is: {pk}")
        logger.info(user)
        manage_groups_form = ManageUserGroupsForm(request.POST, instance=user)

        if manage_groups_form.is_valid():
            manage_groups_form.save()  # This updates the user's groups
            messages.success(request, f"Group memberships for '{user.username}' updated successfully.")
            # Redirect to the admin settings page after success
            return redirect(reverse("settings") + "#manage-users")  # Redirect back to the user tab
        # Form is invalid - store data and errors in session
        request.session["manage_user_groups_form_data"] = request.POST
        messages.error(
            request,
            f"Error updating group memberships for '{user.username}'. Please check the form.",
        )  # Generic error message
        # Redirect back to the GET view for this user's group management page
        # Note: This redirects back to the manage_user_groups view itself, not the main settings page,
        # so the user stays on the correct page to fix errors.
        return redirect(reverse("admin_manage_user_groups", pk=user.pk))


class AddGroupView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, View):
    """
    Handles the creation of a new group via a POST request using PRG pattern.
    Stores form data and errors in session on failure.
    """

    def post(self, request: HttpRequest, *args, **kwargs):  # noqa: ARG002
        add_group_form = AddGroupForm(request.POST)
        if add_group_form.is_valid():
            add_group_form.save()
            messages.success(request, f"Group '{add_group_form.cleaned_data['name']}' created successfully.")
            # Redirect on success - no need to store form data/errors
            return redirect(reverse("settings") + "#manage-groups")
        # Form is invalid - store data and errors in session
        request.session["add_group_form_data"] = request.POST
        messages.error(request, "Error creating group. Please check the form.")  # Generic error message
        # Redirect to the GET view
        return redirect(reverse("settings") + "#manage-groups")


class RemoveGroupView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, View):
    """
    Handles the removal of a group via a POST request.
    """

    def post(self, request: HttpRequest, pk: int, *args, **kwargs):  # noqa: ARG002
        group = get_object_or_404(Group, pk=pk)
        group_name = group.name
        group.delete()
        messages.success(request, f"Group '{group_name}' removed successfully.")
        # Redirect after action
        return redirect(reverse("settings") + "#manage-groups")
