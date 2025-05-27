import logging
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from memoria.common.auth import active_staff_or_superuser_auth
from memoria.routes.groups.schemas import GroupCreateInSchema
from memoria.routes.groups.schemas import GroupOutSchema
from memoria.routes.groups.schemas import GroupUpdateInSchema

router = Router(tags=["groups"])
logger = logging.getLogger(__name__)

UserModelT = get_user_model()


@router.post(
    "/",
    response={HTTPStatus.OK: list[GroupOutSchema]},
    auth=active_staff_or_superuser_auth,
    operation_id="groups_create",
)
def create_group(
    request: HttpRequest,
    data: GroupCreateInSchema | list[GroupCreateInSchema],
):
    """
    Creates multiple groups from a list of group schemas or a single group.

    Args:
        request: The Django request object.
        data: A GroupListInCreateSchema object containing the list of groups to create.

    Returns:
        A list of GroupOutSchema objects representing the created groups.
    """
    if isinstance(data, GroupCreateInSchema):
        data = [data]

    with transaction.atomic():
        return [Group.objects.create(name=group_data.name) for group_data in data]


@router.get(
    "/",
    response={HTTPStatus.OK: list[GroupOutSchema]},
    auth=active_staff_or_superuser_auth,
    operation_id="group_get_all",
)
def get_all_groups(
    request: HttpRequest,
):
    return Group.objects.all()


@router.get(
    "/{group_id}/",
    response={HTTPStatus.OK: GroupOutSchema},
    auth=active_staff_or_superuser_auth,
    operation_id="group_get_single",
)
def get_single_groups(
    request: HttpRequest,
    group_id: int,
):
    return get_object_or_404(Group, pk=group_id)


@router.patch(
    "/{group_id}/",
    response={HTTPStatus.OK: GroupOutSchema},
    auth=active_staff_or_superuser_auth,
    operation_id="group_update_single",
)
def update_single_group(
    request: HttpRequest,
    group_id: int,
    data: GroupUpdateInSchema,
):
    group = get_object_or_404(Group, pk=group_id)
    group.name = data.name
    group.save()
    return group


@router.delete(
    "/{group_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    auth=active_staff_or_superuser_auth,
    operation_id="group_delete_single",
)
def delete_group(
    request: HttpRequest,
    group_id: int,
):
    group = get_object_or_404(Group, pk=group_id)
    group.delete()
    return HTTPStatus.NO_CONTENT, None
