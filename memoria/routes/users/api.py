import logging
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja import Router
from ninja.security import django_auth

from memoria.common.errors import HttpBadRequestError
from memoria.common.errors import HttpNotAuthorizedError
from memoria.routes.authentication.schemas import UserOutSchema
from memoria.routes.users.schemas import UserInCreateSchema

router = Router(tags=["users"])
logger = logging.getLogger(__name__)

UserModelT = get_user_model()


@router.get("/profile/", response=UserOutSchema, auth=django_auth)
def get_profile(
    request: HttpRequest,
):
    return request.user


@router.post("/create/", response={HTTPStatus.OK: UserOutSchema}, auth=django_auth)
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
