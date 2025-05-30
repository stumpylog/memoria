import logging
from http import HTTPStatus

from django.contrib.auth import aauthenticate
from django.contrib.auth import alogin
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as django_logout
from django.http import HttpRequest
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from ninja import Router

from memoria.common.auth import active_user_auth
from memoria.common.errors import HttpNotAuthorizedError
from memoria.routes.authentication.schemas import AuthLoginSchema
from memoria.routes.authentication.schemas import CsrfTokenOutSchema

UserModelT = get_user_model()

router = Router(tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/csrf/", response=CsrfTokenOutSchema, operation_id="auth_get_csrf_token")
@ensure_csrf_cookie
@csrf_exempt
def get_csrf_token(request: HttpRequest):
    return JsonResponse({"csrf_token": get_token(request)})


@router.post(
    "/login/",
    response={HTTPStatus.NO_CONTENT: None},
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
    operation_id="auth_login",
)
async def login(request: HttpRequest, data: AuthLoginSchema):
    user: UserModelT | None = await aauthenticate(
        request,
        username=data.username,
        password=data.password.get_secret_value(),
    )

    if user is not None:
        await alogin(request, user)

        return HTTPStatus.NO_CONTENT, None
    msg = "Invalid credentials. Please try again."
    logger.error(msg)
    raise HttpNotAuthorizedError(msg)


@router.post(
    "/logout/",
    response={HTTPStatus.NO_CONTENT: None},
    auth=active_user_auth,
    operation_id="auth_logout",
)
def logout(request: HttpRequest):
    django_logout(request)
    return HTTPStatus.NO_CONTENT, None
