import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from memoria.common.auth import active_staff_or_superuser_auth
from memoria.common.auth import active_user_auth
from memoria.common.errors import HttpBadRequestError
from memoria.common.errors import HttpNotAuthorizedError
from memoria.routes.groups.schemas import GroupOutSchema
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
    response={HTTPStatus.OK: UserOutSchema},
    auth=active_staff_or_superuser_auth,
    operation_id="user_create",
)
def create_user(
    request: HttpRequest,
    data: UserInCreateSchema,
):
    if data.is_staff and not (request.user.is_staff or request.user.is_superuser):
        raise HttpNotAuthorizedError("Only staff or superusers can create a new staff user")  # noqa: EM101, TRY003
    if data.is_superuser and not request.user.is_superuser:
        raise HttpNotAuthorizedError("Only superusers can create a new superuser")  # noqa: EM101, TRY003
    if data.is_superuser and not data.is_staff:
        logger.warning("Requested creating a non-staff superuser, overriding")
        data.is_staff = True
    if not data.is_superuser:
        new_user: UserModelT = UserModelT.objects.create_user(
            username=data.username,
            email=data.email,
            password=data.password.get_secret_value(),
        )
        if data.is_staff:
            new_user.is_staff = True
            new_user.save()

    else:
        new_user = UserModelT.objects.create_superuser(
            username=data.username,
            email=data.email,
            password=data.password.get_secret_value(),
        )

    if data.first_name:
        new_user.first_name = data.first_name
    if data.last_name:
        new_user.last_name = data.last_name

    return new_user


@router.get(
    "/",
    response=list[UserOutSchema],
    auth=active_staff_or_superuser_auth,
    operation_id="user_get_all",
)
def get_all_users(
    request: HttpRequest,
):
    return UserModelT.objects.all()


@router.get(
    "/me/",
    response=UserOutSchema,
    auth=active_user_auth,
    operation_id="user_get_me",
)
def get_user_me_info(
    request: HttpRequest,
):
    return request.user


@router.get(
    "/{user_id}/info/",
    response=UserOutSchema,
    auth=active_user_auth,
    operation_id="user_get_info",
)
def get_user_info(
    request: HttpRequest,
    user_id: int,
):
    user = get_object_or_404(UserModelT, pk=user_id)
    return user


@router.get(
    "/me/profile/",
    response=UserProfileOutSchema,
    auth=active_user_auth,
    operation_id="user_get_my_profile",
)
def get_my_profile(
    request: HttpRequest,
):
    return request.user.profile


@router.get(
    "/{user_id}/profile/",
    response=UserProfileOutSchema,
    auth=active_user_auth,
    operation_id="user_get_profile",
)
def get_profile(
    request: HttpRequest,
    user_id: int,
):
    user = get_object_or_404(UserModelT.objects.select_related("profile"), pk=user_id)
    return user.profile


@router.get("/{user_id}/groups/", response=list[GroupOutSchema], auth=active_user_auth, operation_id="user_get_groups")
def get_user_groups(request: HttpRequest, user_id: int):
    user = get_object_or_404(UserModelT.objects.prefetch_related("groups"), id=user_id)
    groups = user.groups.all()
    return [{"id": group.id, "name": group.name} for group in groups]


@router.patch(
    "/{user_id}/info/",
    response=UserOutSchema,
    auth=active_user_auth,
    operation_id="user_set_info",
)
def set_user_info(
    request: HttpRequest,
    user_id: int,
    data: UserUpdateInScheme,
):
    user: UserModelT = get_object_or_404(UserModelT, pk=user_id)
    if data.first_name:
        user.first_name = data.first_name
    if data.last_name:
        user.last_name = data.last_name
    if data.email:
        user.email = data.email
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_staff is not None:
        if not (request.user.is_staff or request.user.is_superuser):
            raise HttpNotAuthorizedError("Only a staff or superuser may designate another staff")
        user.is_staff = data.is_staff
    if data.is_superuser is not None:
        if data.is_superuser and not request.user.is_superuser:
            raise HttpNotAuthorizedError("Only a superuser may designate another super user")
        data.is_superuser = data.is_superuser
    user.save()
    if data.password:
        user.set_password(data.password.get_secret_value())
        user.save()
    return user


@router.patch(
    "/{user_id}/profile/",
    response=UserProfileOutSchema,
    auth=active_user_auth,
    operation_id="user_edit_profile",
)
def edit_profile(
    request: HttpRequest,
    user_id: int,
    data: UserProfileUpdateSchema,
):
    user: UserModelT = get_object_or_404(UserModelT.objects.select_related("profile"), pk=user_id)
    if request.user.id != user.id and not (request.user.is_superuser or request.user.is_staff):
        raise HttpNotAuthorizedError("Cannot edit another user's profile")
    if TYPE_CHECKING:
        assert isinstance(user.profile, UserProfile)
    if data.bio:
        user.profile.bio = data.bio
    if data.timezone_name and (data.timezone_name != user.profile.timezone):
        user.profile.timezone = data.timezone_name
    if data.items_per_page and (data.items_per_page != user.profile.items_per_page):
        user.profile.items_per_page = data.items_per_page
    user.profile.save()
    return request.user


@router.patch(
    "/{user_id}/groups/",
    response=list[GroupOutSchema],
    auth=active_staff_or_superuser_auth,
    operation_id="user_set_groups",
    openapi_extra={
        "responses": {
            HTTPStatus.BAD_REQUEST: {
                "description": "some provided groups don't exist",
            },
        },
    },
)
def set_user_groups(request: HttpRequest, user_id: int, data: list[UserGroupAssignInSchema]):
    user = get_object_or_404(UserModelT.objects.prefetch_related("groups"), id=user_id)

    group_ids = [item.id for item in data]
    groups_to_assign = Group.objects.filter(id__in=group_ids)
    if len(groups_to_assign) != len(group_ids):
        existing_group_ids = {group.id for group in groups_to_assign}
        missing_ids = set(group_ids) - existing_group_ids
        raise HttpBadRequestError(f"Group(s) with ID(s) {missing_ids} do not exist.")

    user.groups.clear()
    user.groups.add(*groups_to_assign)
    groups = user.groups.all()
    return [{"id": group.id, "name": group.name} for group in groups]
