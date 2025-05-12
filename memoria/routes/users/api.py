import logging
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth

from memoria.common.errors import HttpBadRequestError
from memoria.common.errors import HttpNotAuthorizedError
from memoria.routes.users.schemas import GroupAssignSchema
from memoria.routes.users.schemas import GroupOut
from memoria.routes.users.schemas import UserInCreateSchema
from memoria.routes.users.schemas import UserOutSchema
from memoria.routes.users.schemas import UserProfileOutSchema
from memoria.routes.users.schemas import UserProfileUpdateSchema
from memoria.routes.users.schemas import UserUpdateInScheme

router = Router(tags=["users"])
logger = logging.getLogger(__name__)

UserModelT = get_user_model()


@router.get("/profile/", response=UserProfileOutSchema, auth=django_auth, operation_id="user_get_profile")
def get_profile(
    request: HttpRequest,
):
    return request.user.profile


@router.post("/profile/edit/", response=UserProfileOutSchema, auth=django_auth, operation_id="user_edit_profile")
def edit_profile(
    request: HttpRequest,
    data: UserProfileUpdateSchema,
):
    # TODO
    return request.user


@router.get("/me/", response=UserOutSchema, auth=django_auth, operation_id="user_get_info")
def get_user_info(
    request: HttpRequest,
):
    return request.user


@router.post("/me/edit/", response=UserOutSchema, auth=django_auth, operation_id="user_edit_info")
def edit_user_info(
    request: HttpRequest,
    data: UserUpdateInScheme,
):
    return request.user


@router.get("/{user_id}/groups", response=list[GroupOut], auth=django_auth, operation_id="user_get_groups")
def get_user_groups(request: HttpRequest, user_id: int):
    user = get_object_or_404(UserModelT, id=user_id)
    groups = user.groups.all()
    return [{"id": group.id, "name": group.name} for group in groups]


@router.get(
    "/{user_id}/groups",
    response=list[GroupOut],
    auth=django_auth,
    operation_id="user_set_groups",
    openapi_extra={
        "responses": {
            HTTPStatus.BAD_REQUEST: {
                "description": "some provided groups don't exist",
            },
            HTTPStatus.UNAUTHORIZED: {
                "description": "only staff or superusers can assign new groups",
            },
        },
    },
)
def set_user_groups(request: HttpRequest, user_id: int, data: GroupAssignSchema):
    if not request.user.is_staff or not request.user.is_superuser:
        raise HttpNotAuthorizedError("only staff or superusers can assign new groups")

    user = get_object_or_404(UserModelT, id=user_id)

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


@router.post("/create/", response={HTTPStatus.OK: UserOutSchema}, auth=django_auth, operation_id="user_create")
async def create_user(
    request: HttpRequest,
    data: UserInCreateSchema,
):
    if not request.user.is_active:
        raise HttpBadRequestError("Only an active user may create users")  # noqa: EM101, TRY003
    if data.is_staff and not (request.user.is_staff or request.user.is_superuser):
        raise HttpNotAuthorizedError("Only staff or superusers can create a new staff user")  # noqa: EM101, TRY003
    if data.is_superuser and not request.user.is_superuser:
        raise HttpNotAuthorizedError("Only superusers can create a new superuser")  # noqa: EM101, TRY003
    if data.is_superuser and not data.is_staff:
        logger.warning("Requested creating a non-staff superuser, overriding")
        data.is_staff = True
    if not data.is_superuser:
        new_user: UserModelT = await UserModelT.objects.acreate_user(
            username=data.username,
            email=data.email,
            password=data.password,
        )
        if data.is_staff:
            new_user.is_staff = True
            await new_user.asave()
    else:
        new_user = UserModelT.objects.acreate_superuser(
            username=data.username,
            email=data.email,
            password=data.password,
        )
    return new_user
