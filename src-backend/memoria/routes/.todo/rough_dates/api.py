import logging
from http import HTTPStatus

from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Router
from ninja.pagination import PageNumberPagination
from ninja.pagination import paginate

from memoria.common.errors import HttpConflictError
from memoria.common.errors import HttpUnprocessableEntityError
from memoria.models import RoughDate
from memoria.routes.rough_dates.schema import RoughDateCreateInSchema
from memoria.routes.rough_dates.schema import RoughDateReadOutSchema
from memoria.routes.rough_dates.schema import RoughDateUpdateInSchema

router = Router(tags=["dates"])

logger = logging.getLogger(__name__)


@router.get("/", response=list[RoughDateReadOutSchema], operation_id="get_rough_dates")
@paginate(PageNumberPagination)
def get_all_dates(
    request: HttpRequest,  # noqa: ARG001
):
    return RoughDate.objects.all()


@router.get(
    "/{date_id}/",
    response=RoughDateReadOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_single_rough_date",
)
async def get_single_rough_date(
    request: HttpRequest,  # noqa: ARG001
    date_id: int,
):
    instance: RoughDate = await aget_object_or_404(RoughDate, id=date_id)
    return instance


@router.post(
    "/",
    response={HTTPStatus.CREATED: RoughDateReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.BAD_REQUEST: {
                "description": "Date Already Exists",
            },
        },
    },
    operation_id="create_rough_date",
)
async def create_rough_date(
    request: HttpRequest,  # noqa: ARG001
    data: RoughDateCreateInSchema,
):
    rough_date_exists = await RoughDate.objects.filter(
        date=data.date,
        month_valid=data.month_valid,
        day_valid=data.day_valid,
    ).aexists()
    if rough_date_exists:
        msg = f"Date at {data.date} already exists"
        logger.error(msg)
        raise HttpConflictError(msg)
    instance: RoughDate = await RoughDate.objects.acreate(
        date=data.date,
        month_valid=data.month_valid,
        day_valid=data.day_valid,
    )
    return HTTPStatus.CREATED, instance


@router.patch(
    "/{date_id}/",
    response={HTTPStatus.OK: RoughDateReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_rough_date",
)
async def update_rough_date(
    request: HttpRequest,  # noqa: ARG001
    date_id: int,
    data: RoughDateUpdateInSchema,
):
    instance: RoughDate = await aget_object_or_404(RoughDate, id=date_id)
    if data.date is not None:
        instance.date = data.date
    if data.month_valid is not None:
        instance.month_valid = data.month_valid
    if data.day_valid is not None:
        instance.day_valid = data.day_valid
    if instance.day_valid and not instance.month_valid:
        msg = "Cannot set a valid day without a valid month"
        logger.error(msg)
        raise HttpUnprocessableEntityError(msg)
    await instance.asave()
    await instance.arefresh_from_db()
    return instance


@router.delete(
    "/{date_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_rough_date",
)
async def delete_rough_date(
    request: HttpRequest,  # noqa: ARG001
    date_id: int,
):
    instance: RoughDate = await aget_object_or_404(RoughDate, id=date_id)
    await instance.adelete()
    return HTTPStatus.NO_CONTENT, None
