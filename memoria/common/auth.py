import logging
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyCookie

logger = logging.getLogger(__name__)


class SessionAuthIsActive(APIKeyCookie):
    """
    Reusing Django session authentication & verify that the user is an active user
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        if request.user.is_authenticated and request.user.is_active:
            return request.user

        return None


class SessionAuthIsActiveStaff(SessionAuthIsActive):
    """
    Reusing Django session authentication & verify that the user is an active staff user
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        user = super().authenticate(request, key)
        if user is not None and request.user.is_staff:
            return request.user

        return user


class SessionAuthIsActiveSuperUser(SessionAuthIsActive):
    """
    Reusing Django session authentication & verify that the user is an active super user
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        user = super().authenticate(request, key)
        if user is not None and request.user.is_superuser:
            return request.user

        return user


class SessionAuthIsActiveSuperUserOrStaff(SessionAuthIsActive):
    """
    Reusing Django session authentication & verify that the user is an active super user or staff member
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        user = super().authenticate(request, key)
        if user is not None and (request.user.is_superuser or request.user.is_staff):
            return request.user

        return user


# Async-first authentication classes
class AsyncSessionAuthIsActive(APIKeyCookie):
    """
    Async-first session authentication for active users
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        def _sync_auth():
            if request.user.is_authenticated and request.user.is_active:
                return request.user
            return None

        return await sync_to_async(_sync_auth, thread_sensitive=True)()


class AsyncSessionAuthIsActiveStaff(APIKeyCookie):
    """
    Async-first session authentication for staff users
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        def _sync_auth():
            if request.user.is_authenticated and request.user.is_active and request.user.is_staff:
                return request.user
            return None

        return await sync_to_async(_sync_auth, thread_sensitive=True)()


class AsyncSessionAuthIsActiveSuperUser(APIKeyCookie):
    """
    Async-first session authentication for superusers
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        def _sync_auth():
            if request.user.is_authenticated and request.user.is_active and request.user.is_superuser:
                return request.user
            return None

        return await sync_to_async(_sync_auth, thread_sensitive=True)()


class AsyncSessionAuthIsActiveSuperUserOrStaff(APIKeyCookie):
    """
    Async-first session authentication for superusers or staf
    f"""

    param_name: str = settings.SESSION_COOKIE_NAME

    async def authenticate(self, request: HttpRequest, key: str | None) -> Any | None:
        def _sync_auth():
            if (
                request.user.is_authenticated
                and request.user.is_active
                and (request.user.is_superuser or request.user.is_staff)
            ):
                return request.user
            return None

        return await sync_to_async(_sync_auth, thread_sensitive=True)()


active_user_auth = SessionAuthIsActive()
active_staff_auth = SessionAuthIsActiveStaff()
active_superuser_auth = SessionAuthIsActiveSuperUser()
active_staff_or_superuser_auth = SessionAuthIsActiveSuperUserOrStaff()
# Async instances
async_active_user_auth = AsyncSessionAuthIsActive()
async_active_staff_auth = AsyncSessionAuthIsActiveStaff()
async_active_superuser_auth = AsyncSessionAuthIsActiveSuperUser()
async_active_staff_or_superuser_auth = AsyncSessionAuthIsActiveSuperUserOrStaff()
