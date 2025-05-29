import logging
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Router

from memoria.common.auth import active_staff_or_superuser_auth
from memoria.common.auth import async_active_staff_or_superuser_auth
from memoria.routes.groups.schemas import GroupCreateInSchema
from memoria.routes.groups.schemas import GroupOutSchema
from memoria.routes.groups.schemas import GroupUpdateInSchema

router = Router(tags=["groups"])
logger = logging.getLogger(__name__)

UserModelT = get_user_model()


@router.post(
    "/",
    response={HTTPStatus.CREATED: list[GroupOutSchema]},
    auth=active_staff_or_superuser_auth,
    operation_id="create_groups",
)
def create_groups(
    request: HttpRequest,
    data: GroupCreateInSchema | list[GroupCreateInSchema],
):
    """
    Creates one or more groups from a list of group schemas or a single group.

    Args:
        request: The Django request object.
        data: A GroupCreateInSchema object or list of GroupCreateInSchema objects.

    Returns:
        A list of GroupOutSchema objects representing the created groups.
    """
    if isinstance(data, GroupCreateInSchema):
        data = [data]

    # Use async transaction context manager
    with transaction.atomic():
        created_groups = []
        group_names = [group_data.name for group_data in data]

        # Get existing groups to avoid duplicates
        existing_names = set(Group.objects.filter(name__in=group_names).values_list("name", flat=True))
        for group_data in data:
            if group_data.name not in existing_names:
                try:
                    # Use get_or_create for additional safety against race conditions
                    group, created = Group.objects.get_or_create(
                        name=group_data.name,
                        defaults={},
                    )
                    if created:
                        created_groups.append(group)
                        logger.info(f"Created new group: {group_data.name}")
                    else:
                        # This handles race condition where group was created between our check and creation
                        logger.info(f"Group already exists (race condition): {group_data.name}")
                except Exception:
                    logger.exception(f"Failed to create group {group_data.name}")
                    # Continue processing other groups instead of failing the entire batch
                    continue
            else:
                logger.info(f"Skipping duplicate group: {group_data.name}")

        return created_groups


@router.get(
    "/",
    response={HTTPStatus.OK: list[GroupOutSchema]},
    auth=async_active_staff_or_superuser_auth,
    operation_id="list_groups",
)
async def list_groups(request: HttpRequest):
    """
    Retrieves all groups.

    Returns:
        A list of GroupOutSchema objects representing all groups.
    """
    # Use async queryset evaluation with prefetch if needed for related data
    groups = Group.objects.all()
    return [group async for group in groups]


@router.get(
    "/{group_id}/",
    response={HTTPStatus.OK: GroupOutSchema},
    auth=async_active_staff_or_superuser_auth,
    operation_id="get_group",
)
async def get_group(
    request: HttpRequest,
    group_id: int,
):
    """
    Retrieves a single group by ID.

    Args:
        group_id: The ID of the group to retrieve.

    Returns:
        A GroupOutSchema object representing the requested group.
    """
    return await aget_object_or_404(Group, pk=group_id)


@router.patch(
    "/{group_id}/",
    response={HTTPStatus.OK: GroupOutSchema},
    auth=async_active_staff_or_superuser_auth,
    operation_id="update_group",
)
async def update_group(
    request: HttpRequest,
    group_id: int,
    data: GroupUpdateInSchema,
):
    """
    Updates a single group's information.

    Args:
        group_id: The ID of the group to update.
        data: The updated group data.

    Returns:
        A GroupOutSchema object representing the updated group.
    """
    group = await aget_object_or_404(Group, pk=group_id)

    # Update fields from schema
    group.name = data.name

    await group.asave()
    return group


@router.delete(
    "/{group_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    auth=async_active_staff_or_superuser_auth,
    operation_id="delete_group",
)
async def delete_group(
    request: HttpRequest,
    group_id: int,
):
    """
    Deletes a single group by ID.

    Args:
        group_id: The ID of the group to delete.

    Returns:
        HTTP 204 No Content on successful deletion.
    """
    group = await aget_object_or_404(Group, pk=group_id)
    await group.adelete()
    return HTTPStatus.NO_CONTENT, None
