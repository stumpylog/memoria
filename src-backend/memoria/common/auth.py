import logging
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyCookie

from memoria.common.errors import HttpForbiddenError

logger = logging.getLogger(__name__)

Forbidden = HttpForbiddenError("You do not have permission to perform this action.")


class SessionAuthIsActive(APIKeyCookie):
    """
    Reusing Django session authentication & verify that the user is an active user
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:  # noqa: ARG002
        if request.user.is_authenticated and request.user.is_active:
            return request.user
        return None


class AsyncSessionAuthIsActive(APIKeyCookie):
    """
    Async-first session authentication for active users
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:  # noqa: ARG002
        @sync_to_async(thread_sensitive=True)
        def _sync_auth():
            if request.user.is_authenticated and request.user.is_active:
                return request.user
            return None

        return await _sync_auth()


# --- MODIFIED: Sync Authorization Classes ---


class SessionAuthIsActiveStaff(SessionAuthIsActive):
    """
    Reusing Django session authentication & verify that the user is an active staff user.
    Returns 403 FORBIDDEN if the user is active but not staff.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        user = super().authenticate(request, key)
        if user is None:
            # User is not authenticated or not active, triggers 401
            return None

        # User is active, now check for staff permission (authorization)
        if not user.is_staff:
            # User is not a staff member, trigger 403
            raise Forbidden

        return user


class SessionAuthIsActiveSuperUser(SessionAuthIsActive):
    """
    Reusing Django session authentication & verify that the user is an active super user.
    Returns 403 FORBIDDEN if the user is active but not a superuser.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        user = super().authenticate(request, key)
        if user is None:
            return None  # Triggers 401

        if not user.is_superuser:
            raise Forbidden  # Triggers 403

        return user


class SessionAuthIsActiveSuperUserOrStaff(SessionAuthIsActive):
    """
    Reusing Django session authentication & verify that the user is an active super user or staff member.
    Returns 403 FORBIDDEN if the user is active but not a superuser or staff.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        user = super().authenticate(request, key)
        if user is None:
            return None  # Triggers 401

        if not (user.is_superuser or user.is_staff):
            raise Forbidden  # Triggers 403

        return user


# --- MODIFIED: Async-first Authorization Classes ---


class AsyncSessionAuthIsActiveStaff(APIKeyCookie):
    """
    Async-first session authentication for staff users.
    Returns 403 FORBIDDEN if the user is active but not staff.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        auth_base = AsyncSessionAuthIsActive()
        user = await auth_base.authenticate(request, key)

        if user is None:
            return None  # Triggers 401

        is_staff = await sync_to_async(getattr)(user, "is_staff")
        if not is_staff:
            raise Forbidden  # Triggers 403

        return user


class AsyncSessionAuthIsActiveSuperUser(APIKeyCookie):
    """
    Async-first session authentication for superusers.
    Returns 403 FORBIDDEN if the user is active but not a superuser.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        auth_base = AsyncSessionAuthIsActive()
        user = await auth_base.authenticate(request, key)

        if user is None:
            return None  # Triggers 401

        is_superuser = await sync_to_async(getattr)(user, "is_superuser")
        if not is_superuser:
            raise Forbidden  # Triggers 403

        return user


class AsyncSessionAuthIsActiveSuperUserOrStaff(APIKeyCookie):
    """
    Async-first session authentication for superusers or staff.
    Returns 403 FORBIDDEN if the user is active but not a superuser or staff.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        auth_base = AsyncSessionAuthIsActive()
        user = await auth_base.authenticate(request, key)

        if user is None:
            return None  # Triggers 401

        is_staff, is_superuser = await sync_to_async(
            lambda u: (u.is_staff, u.is_superuser),
        )(user)

        if not (is_superuser or is_staff):
            raise Forbidden  # Triggers 403

        return user


active_user_auth = SessionAuthIsActive()
active_staff_auth = SessionAuthIsActiveStaff()
active_superuser_auth = SessionAuthIsActiveSuperUser()
active_staff_or_superuser_auth = SessionAuthIsActiveSuperUserOrStaff()
# Async instances
async_active_user_auth = AsyncSessionAuthIsActive()
async_active_staff_auth = AsyncSessionAuthIsActiveStaff()
async_active_superuser_auth = AsyncSessionAuthIsActiveSuperUser()
async_active_staff_or_superuser_auth = AsyncSessionAuthIsActiveSuperUserOrStaff()
