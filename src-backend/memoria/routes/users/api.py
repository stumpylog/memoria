import logging
from http import HTTPStatus
from typing import TYPE_CHECKING
from typing import Literal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Query
from ninja import Router

from memoria.common.auth import active_staff_or_superuser_auth
from memoria.common.auth import active_user_auth
from memoria.common.auth import async_active_staff_or_superuser_auth
from memoria.common.auth import async_active_user_auth
from memoria.common.errors import HttpBadRequestError
from memoria.common.errors import HttpConflictError
from memoria.common.errors import HttpForbiddenError
from memoria.routes.groups.schemas import GroupOutSchema
from memoria.routes.users.schemas import UserFilterSchema
from memoria.routes.users.schemas import UserGroupAssignInSchema
from memoria.routes.users.schemas import UserInCreateSchema
from memoria.routes.users.schemas import UserOutSchema
from memoria.routes.users.schemas import UserProfileOutSchema
from memoria.routes.users.schemas import UserProfileUpdateSchema
from memoria.routes.users.schemas import UserUpdateInScheme

if TYPE_CHECKING:
    from memoria.models import UserProfile

router = Router(tags=["users"])
logger = logging.getLogger(__name__)

UserModelT = get_user_model()


@router.post(
    "/",
    response={HTTPStatus.CREATED: UserOutSchema},
    auth=async_active_staff_or_superuser_auth,
    operation_id="users_create",
)
async def users_create(
    request: HttpRequest,
    data: UserInCreateSchema,
):
    """
    Create a new user with proper permission checks and validation.
    """
    if data.is_superuser and not request.user.is_superuser:
        raise HttpForbiddenError("Only superusers can create superusers")

    # superusers must be staff
    if data.is_superuser and not data.is_staff:
        logger.warning("Creating superuser as staff (superusers must be staff)")
        data.is_staff = True

    filters = Q(username=data.username)
    if data.email:
        filters |= Q(email=data.email)

    existing_user = await UserModelT.objects.filter(filters).afirst()

    if existing_user is not None:
        # Determine which field caused the conflict for a more specific error message
        if existing_user.username == data.username:
            raise HttpConflictError("Username already taken")
        if data.email and existing_user.email == data.email:
            raise HttpConflictError("Email already taken")

    # Create user asynchronously
    if data.is_superuser:
        new_user = await UserModelT.objects.acreate_superuser(
            username=data.username,
            email=data.email,
            password=data.password.get_secret_value(),
        )
    else:
        new_user = await UserModelT.objects.acreate_user(
            username=data.username,
            email=data.email,
            password=data.password.get_secret_value(),
        )

        if data.is_staff:
            new_user.is_staff = True
    new_user.is_active = data.is_active

    # Set optional fields
    if data.first_name:
        new_user.first_name = data.first_name
    if data.last_name:
        new_user.last_name = data.last_name

    # Save all changes
    await new_user.asave()
    return new_user


@router.get(
    "/",
    response=list[UserOutSchema],
    auth=active_staff_or_superuser_auth,
    operation_id="users_list",
)
def users_list(
    request: HttpRequest,
    filters: UserFilterSchema = Query(...),
    sort_by: Literal["username", "pk"] = Query("pk", description="Field to sort by: 'username' or 'id'. "),
):
    """
    Get all users with filtering and pagination.
    """
    queryset = UserModelT.objects.all()
    queryset = filters.filter(queryset)
    return queryset.order_by("sort_by")


@router.get(
    "/me/",
    response=UserOutSchema,
    auth=active_user_auth,
    operation_id="users_get_current",
)
def users_get_current(request: HttpRequest):
    """Get current user's information."""
    return request.user


@router.get(
    "/{user_id}/info/",
    response=UserOutSchema,
    auth=async_active_user_auth,
    operation_id="users_get_by_id",
)
async def users_get_by_id(request: HttpRequest, user_id: int):
    """
    Get user information with proper permission checks.
    """
    user = await aget_object_or_404(UserModelT, pk=user_id)

    # Permission check: users can only view their own info unless staff/superuser
    if request.user.pk != user.pk and not (request.user.is_staff or request.user.is_superuser):
        raise HttpForbiddenError("Cannot view another user's information")

    return user


@router.get(
    "/me/profile/",
    response=UserProfileOutSchema,
    auth=async_active_user_auth,
    operation_id="users_profile_get_current",
)
async def users_profile_get_current(request: HttpRequest):
    """
    Get current user's profile.
    """
    user = await UserModelT.objects.select_related("profile").aget(pk=request.user.id)
    return user.profile


@router.get(
    "/{user_id}/profile/",
    response=UserProfileOutSchema,
    auth=async_active_user_auth,
    operation_id="users_profile_get_by_id",
)
async def users_profile_get_by_id(request: HttpRequest, user_id: int):
    """
    Get user profile with permission checks.
    """
    user = await aget_object_or_404(
        UserModelT.objects.select_related("profile"),
        pk=user_id,
    )

    # Permission check: users can only view their own profile unless staff/superuser
    if request.user.id != user.id and not (request.user.is_staff or request.user.is_superuser):
        raise HttpForbiddenError("Cannot view another user's profile")

    return user.profile


@router.get(
    "/{user_id}/groups/",
    response=list[GroupOutSchema],
    auth=async_active_user_auth,
    operation_id="users_groups_list",
)
async def users_groups_list(request: HttpRequest, user_id: int):
    """Get user's groups with permission checks."""
    # Permission check
    if request.user.pk != user_id and not (request.user.is_staff or request.user.is_superuser):
        raise HttpForbiddenError("Cannot view another user's groups")

    user = await aget_object_or_404(
        UserModelT.objects.prefetch_related("groups"),
        id=user_id,
    )

    # Use async iteration for the groups
    return [GroupOutSchema(id=group.id, name=group.name) async for group in user.groups.all()]


@router.patch(
    "/{user_id}/info/",
    response=UserOutSchema,
    auth=async_active_user_auth,
    operation_id="users_update",
)
async def users_update(
    request: HttpRequest,
    user_id: int,
    data: UserUpdateInScheme,
):
    """
    Update user information with proper permission and validation checks.
    """
    user = await aget_object_or_404(UserModelT, pk=user_id)

    # Permission check: users can only edit their own info unless staff/superuser
    if request.user.pk != user.pk and not (request.user.is_staff or request.user.is_superuser):
        raise HttpForbiddenError("Cannot edit another user's information")

    # Update basic fields
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.email is not None:
        user.email = data.email
    if data.is_active is not None:
        user.is_active = data.is_active

    # Permission checks for staff/superuser changes
    if data.is_staff is not None:
        if not (request.user.is_staff or request.user.is_superuser):
            raise HttpForbiddenError("Only staff or superusers may designate staff status")
        user.is_staff = data.is_staff

    if data.is_superuser is not None:
        if not request.user.is_superuser:
            raise HttpForbiddenError("Only superusers may designate superuser status")
        user.is_superuser = data.is_superuser
        # Ensure superusers are also staff
        if data.is_superuser and not user.is_staff:
            user.is_staff = True

    await user.asave()

    # Handle password separately to ensure it's hashed
    if data.password:
        user.set_password(data.password.get_secret_value())
        await user.asave()

    return user


@router.patch(
    "/{user_id}/profile/",
    response=UserProfileOutSchema,
    auth=async_active_user_auth,
    operation_id="users_profile_update",
)
async def users_profile_update(
    request: HttpRequest,
    user_id: int,
    data: UserProfileUpdateSchema,
):
    """
    Edit user profile with permission checks.
    """
    user = await aget_object_or_404(
        UserModelT.objects.select_related("profile"),
        pk=user_id,
    )

    # Permission check
    if request.user.pk != user.pk and not (request.user.is_superuser or request.user.is_staff):
        raise HttpForbiddenError("Cannot edit another user's profile")

    if TYPE_CHECKING:
        assert isinstance(user.profile, UserProfile)

    # Update profile fields
    profile_updated = False
    if data.bio is not None:
        user.profile.bio = data.bio
        profile_updated = True

    if data.timezone_name and data.timezone_name != user.profile.timezone:
        user.profile.timezone = data.timezone_name
        profile_updated = True

    if data.items_per_page and data.items_per_page != user.profile.items_per_page:
        user.profile.items_per_page = data.items_per_page
        profile_updated = True

    if profile_updated:
        await user.profile.asave()

    return user.profile


@router.patch(
    "/{user_id}/groups/",
    response=list[GroupOutSchema],
    auth=async_active_staff_or_superuser_auth,
    operation_id="users_groups_update",
    openapi_extra={
        "responses": {
            HTTPStatus.BAD_REQUEST: {
                "description": "Some provided groups don't exist",
            },
        },
    },
)
async def users_groups_update(
    request: HttpRequest,
    user_id: int,
    data: list[UserGroupAssignInSchema],
):
    """Set user's groups with validation."""
    user = await aget_object_or_404(
        UserModelT.objects.prefetch_related("groups"),
        id=user_id,
    )

    if not data:
        # Clear all groups if empty list provided
        await user.groups.aclear()
        return []

    group_ids = [item.id for item in data]

    # Validate all groups exist in a single query
    existing_groups = [group async for group in Group.objects.filter(id__in=group_ids)]

    existing_group_ids = {group.id for group in existing_groups}
    missing_ids = set(group_ids) - existing_group_ids

    if missing_ids:
        raise HttpBadRequestError(f"Group(s) with ID(s) {sorted(missing_ids)} do not exist")

    # Update user's groups
    await user.groups.aclear()
    await user.groups.aadd(*existing_groups)

    # Return updated groups
    return [GroupOutSchema(id=group.id, name=group.name) async for group in user.groups.all()]
