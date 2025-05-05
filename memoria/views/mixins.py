import logging
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import cast

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Q
from django.http import HttpRequest

from memoria.models import UserProfile
from memoria.models.abstract import AccessModelMixin

User = get_user_model()

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

# Create a type variable for the view
ViewT = TypeVar("ViewT")


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


class AccessQuerysetMixin:
    """Mixin to filter any AccessMixin-derived model by user permissions."""

    request: HttpRequest

    def get_queryset(self):
        qs = super().get_queryset()

        user = cast("AbstractUser", self.request.user)

        if not user.is_active:
            return qs.none()
        if user.is_superuser:
            return qs

        if TYPE_CHECKING:
            self.model = cast("AccessModelMixin", self.model)

        group_ids = list(user.groups.only("pk").values_list("pk", flat=True))
        view_through = self.model.view_groups.through
        edit_through = self.model.edit_groups.through

        # Subqueries to check membership
        can_view = Exists(
            view_through.objects.filter(
                **{f"{self.model._meta.model_name}_id": OuterRef("pk")},
                group_id__in=group_ids,
            ),
        )
        can_edit = Exists(
            edit_through.objects.filter(
                **{f"{self.model._meta.model_name}_id": OuterRef("pk")},
                group_id__in=group_ids,
            ),
        )

        # Open if no groups assigned
        open_q = Q(view_group_count=0, edit_group_count=0)

        # Annotate and filter
        return (
            qs.annotate(can_view=can_view | open_q, can_edit=can_edit)
            .filter(Q(can_view=True) | Q(can_edit=True))
            .distinct()
        )
