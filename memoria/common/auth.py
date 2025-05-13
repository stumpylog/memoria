from typing import Any

from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyCookie


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


active_user_auth = SessionAuthIsActive()
active_staff_auth = SessionAuthIsActiveStaff()
active_superuser_auth = SessionAuthIsActiveSuperUser()
active_staff_or_superuser_auth = SessionAuthIsActiveSuperUserOrStaff()
