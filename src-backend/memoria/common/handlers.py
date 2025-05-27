from http import HTTPStatus

from django.http import HttpRequest
from django.http import JsonResponse


def custom404(request: HttpRequest, exception=None):  # noqa: ARG001
    resp = JsonResponse(
        {
            "status_code": HTTPStatus.NOT_FOUND,
            "error": f'The resource "{request.path}" was not found',
        },
    )
    resp.status_code = HTTPStatus.NOT_FOUND
    return resp
