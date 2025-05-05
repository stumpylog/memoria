from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm

from memoria.models.abstract import AccessControlledModel


def assign_object_permission(
    permission: str,
    obj: AccessControlledModel,
    users_or_groups: User | Group | list[User | Group],
) -> None:
    """
    Assigns permission to users or groups for the given object.

    Args:
        permission: Permission enum value to assign
        obj: The object to assign permission for
        users_or_groups: User(s) or Group(s) to assign permission to
    """
    if not isinstance(users_or_groups, list):
        users_or_groups = [users_or_groups]

    for user_or_group in users_or_groups:
        assign_perm(permission, user_or_group, obj)


def remove_object_permission(
    permission: str,
    obj: AccessControlledModel,
    users_or_groups: User | Group | list[User | Group],
) -> None:
    """
    Removes permission from users or groups for the given object.

    Args:
        permission: Permission enum value to remove
        obj: The object to remove permission from
        users_or_groups: User(s) or Group(s) to remove permission from
    """
    if not isinstance(users_or_groups, list):
        users_or_groups = [users_or_groups]

    for user_or_group in users_or_groups:
        remove_perm(permission, user_or_group, obj)
