import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import cast

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.http import HttpRequest

from memoria.models import UserProfile

User = get_user_model()

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


class BaseUserAuthMixin(UserPassesTestMixin):
    """Base mixin that ensures a user is active and has specific permissions."""

    request: HttpRequest

    def test_active_and_role(self, *, is_staff: bool = False, is_superuser: bool = False) -> bool:
        """
        Test if user is active and meets the specified role requirements.

        Args:
            is_staff: Whether the user needs to be staff
            is_superuser: Whether the user needs to be superuser

        Returns:
            True if user meets all requirements, False otherwise
        """
        user = cast("AbstractUser", self.request.user)

        if not user.is_active:
            return False

        if is_superuser and user.is_superuser:
            return True

        if is_staff and user.is_staff:
            return True

        # If specific permissions required but user has none
        if (is_staff or is_superuser) and not (user.is_staff or user.is_superuser):
            return False

        # Default case when no specific permissions required (just active)
        return not (is_staff or is_superuser)


class StaffRequiredMixin(BaseUserAuthMixin):
    """Mixin that ensures a user is active and staff."""

    def test_func(self) -> bool:
        return self.test_active_and_role(is_staff=True)


class SuperuserRequiredMixin(BaseUserAuthMixin):
    """Mixin that ensures a user is active and superuser."""

    def test_func(self) -> bool:
        return self.test_active_and_role(is_superuser=True)


class StaffOrSuperuserRequiredMixin(BaseUserAuthMixin):
    """Mixin that ensures a user is active and either staff or superuser."""

    def test_func(self) -> bool:
        return self.test_active_and_role(is_staff=True, is_superuser=True)


class DefaultPaginationMixin:
    default_paginate_by = UserProfile.ImagesPerPageChoices.THIRTY

    request: HttpRequest

    def get_paginate_by(self, queryset) -> int:  # noqa: ARG002
        """
        Dynamically determine paginate_by based on user profile.
        """
        user = cast("AbstractUser", self.request.user)

        try:
            # Assuming your User has a one-to-one field named 'profile'
            # that links to your Profile model, and Profile has a field
            # 'items_per_page'. Adjust attribute names as needed.
            profile: UserProfile = user.profile
            user_preference: int = profile.items_per_page

            # Basic validation: ensure the preference is a positive integer
            if isinstance(user_preference, int) and user_preference > 0:
                return user_preference
            # Handle cases where the preference is invalid
            logger.warning(
                f"Invalid pagination preference ({user_preference}) for user {user.username}. Using default.",
            )

        except UserProfile.DoesNotExist:
            # Handle the case where the user does not have a profile
            logger.warning(f"Profile not found for user {user.username}. Using default paginate_by.")
        except AttributeError:
            # Handle case if the 'items_per_page' field doesn't exist on the Profile
            logger.warning(
                f"'items_per_page' field not found on Profile for user {user.username}. Using default paginate_by.",
            )
        except Exception:
            # Catch any other potential errors during profile access
            logger.exception(f"Error accessing profile pagination preference for user {user.username}: Using default.")

        # If the user is not authenticated (though LoginRequiredMixin should prevent this)
        # or if profile access fails, fall back to the default
        return self.default_paginate_by


class ObjectPermissionViewMixin:
    """
    CBV mixin to enforce object-level view/edit permissions.
    Set `permission_type` to 'view' or 'edit' in subclasses.
    Editors (edit permission) also implicitly have view permission.
    """

    permission_type: str  # 'view' or 'edit'

    def get_queryset(self):
        user = self.request.user
        base_qs = super().get_queryset()
        if not user.is_active:
            return base_qs.none()
        if user.is_superuser:
            return base_qs

        groups = user.groups.all()

        # No groups set, anyone can access
        open_to_all_filter = Q(edit_groups__isnull=True) & Q(view_groups__isnull=True)
        # User is in the one or more view groups
        can_view_filter = Q(view_groups__in=groups)
        # User is in one or more edit groups
        can_edit_filter = Q(edit_groups__in=groups)

        if self.permission_type == "view":
            # include objects open to all, viewers, or editors
            return base_qs.filter(open_to_all_filter | can_view_filter | can_edit_filter).distinct()

        # edit permission: open to all editors or specific editors
        return base_qs.filter(open_to_all_filter | can_edit_filter).distinct()

    def has_object_permission(self, obj: Any) -> dict[Literal["can_view", "can_edit"], bool]:
        user = self.request.user
        if not user.is_active:
            return {"can_view": False, "can_edit": False}
        if user.is_superuser:
            return {"can_view": True, "can_edit": True}

        user_groups = user.groups.all().only("pk")

        user_in_edit_groups: bool = obj.edit_groups.filter(pk__in=user_groups).exists()
        user_in_view_groups: bool = obj.view_groups.filter(pk__in=user_groups).exists()

        obj_requires_edit_group: bool = obj.edit_groups.exists()
        obj_requires_view_group: bool = obj.view_groups.exists()

        # User can edit if:
        # 1. The object has no edit groups specified (meaning anyone can edit by default)
        # OR
        # 2. The object *does* have edit groups, AND the user is in one of them
        can_edit = (not obj_requires_edit_group) or user_in_edit_groups

        # User can view if:
        # 1. They can edit (edit permission implies view permission)
        # OR
        # 2. The object has no view groups specified (meaning anyone can view by default)
        # OR
        # 3. The object *does* have view groups, AND the user is in one of the view groups
        can_view = can_edit or (not obj_requires_view_group) or user_in_view_groups

        return {"can_view": can_view, "can_edit": can_edit}
