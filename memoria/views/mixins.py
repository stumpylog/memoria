from typing import TYPE_CHECKING
from typing import TypeVar
from typing import cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest

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
