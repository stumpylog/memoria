import logging
from http import HTTPStatus

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils import timezone
from ninja import Form
from ninja import Router
from scansteward.common.authentication import AuthApiKey
from scansteward.common.errors import HttpNotAuthorizedError
from scansteward.models import Token
from scansteward.routes.authentication.schemas import TokenReadOutSchema
from scansteward.routes.users.schemas import UserInCreateSchema
from scansteward.routes.users.schemas import UserOutCreateResponse
from scansteward.routes.users.schemas import UserOutProfileResponse
from scansteward.routes.users.schemas import UserType

router = Router(tags=["users"])
logger = logging.getLogger(__name__)


@router.post(
    "/login/",
    response={HTTPStatus.OK: TokenReadOutSchema},
)
def login_user(
    request: HttpRequest,
    username: Form[str],
    password: Form[str],
):
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        user.profile.last_login = timezone.now()
        user.profile.save()
        token = Token.objects.create(user=user)
        return {"token": token.key}
    raise HttpNotAuthorizedError


@router.post("/logout", response={HTTPStatus.OK: dict}, auth=AuthApiKey())
def logout_user(
    request: HttpRequest,
):
    # Invalidate the current token
    request.auth.delete()
    # Logout the user from the session
    logout(request)
    return HTTPStatus.OK, {"message": "Successfully logged out"}


@router.get("/profile/", response=UserOutProfileResponse, auth=AuthApiKey())
def get_profile(
    request: HttpRequest,
):
    user = request.auth.user
    return UserOutProfileResponse(
        username=user.username,
        last_login=user.profile.last_login if user.profile.last_login else None,
    )


@router.post("/create/", response={HTTPStatus.OK: UserOutCreateResponse}, auth=AuthApiKey())
def create_user(
    request: HttpRequest,
    data: UserInCreateSchema,
):
    match data.user_type:
        case UserType.Regular:
            instance = User.objects.create_user(
                first_name=data.first_name,
                last_name=data.last_name,
                username=data.username,
                password=data.username,
                email=data.email,
            )
        case UserType.Staff:
            if not (request.user.is_staff or request.user.is_superuser):
                raise HttpNotAuthorizedError("Only staff or superusers can create a new staf user")  # noqa: EM101, TRY003
            instance = User.objects.create_user(
                first_name=data.first_name,
                last_name=data.last_name,
                username=data.username,
                password=data.username,
                email=data.email,
            )
            instance.is_staff = True
            instance.save()
        case UserType.Superuser:
            if not request.user.is_superuser:
                raise HttpNotAuthorizedError("Only superusers can create a new superuser")  # noqa: EM101, TRY003
            instance = User.objects.create_superuser(
                first_name=data.first_name,
                last_name=data.last_name,
                username=data.username,
                password=data.username,
                email=data.email,
            )
    return {"id_": instance.pk}
