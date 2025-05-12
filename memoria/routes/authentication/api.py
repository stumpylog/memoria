import logging
from http import HTTPStatus

from django.contrib.auth import aauthenticate
from django.contrib.auth import alogin
from django.contrib.auth import alogout
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from ninja import Router
from ninja.security import django_auth
from orjson import loads

from memoria.common.errors import HttpBadRequestError
from memoria.common.errors import HttpNotAuthorizedError
from memoria.routes.authentication.schemas import CsrfTokenOutSchema
from memoria.routes.authentication.schemas import UserOutSchema

UserModelT = get_user_model()

router = Router(tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/csrf/", response=CsrfTokenOutSchema)
@ensure_csrf_cookie
@csrf_exempt
def get_csrf_token(request: HttpRequest):
    return {"csrf_token": get_token(request)}


@router.post(
    "/login/",
    response=UserOutSchema,
    auth=None,
    openapi_extra={
        "responses": {
            HTTPStatus.BAD_REQUEST: {
                "description": "username or password not provided",
            },
            HTTPStatus.UNAUTHORIZED: {
                "description": "invalid username or password provided",
            },
        },
    },
)
async def login(request):
    data = loads(request.body)
    username: str | None = data.get("username")
    password: str | None = data.get("password")

    if not username or not password:
        raise HttpBadRequestError("Please provide both username and password")

    user: UserModelT | None = await aauthenticate(request, username=username, password=password)

    if user is not None:
        await alogin(request, user)

        return user
    raise HttpNotAuthorizedError("Invalid credentials. Please try again.")


@router.post(
    "/logout/",
    response={HTTPStatus.NO_CONTENT: None},
    auth=django_auth,
)
async def logout(request: HttpRequest):
    await alogout(request)
    return HTTPStatus.NO_CONTENT, None
