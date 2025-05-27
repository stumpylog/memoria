import logging
from http import HTTPStatus

from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Router
from ninja.pagination import PageNumberPagination
from ninja.pagination import paginate
from scansteward.common.errors import HttpConflictError
from scansteward.models import ImageSource
from scansteward.routes.sources.schema import ImageSourceCreateInSchema
from scansteward.routes.sources.schema import ImageSourceReadOutSchema
from scansteward.routes.sources.schema import ImageSourceUpdateInSchema

router = Router(tags=["sources"])

logger = logging.getLogger(__name__)


@router.get("/", response=list[ImageSourceReadOutSchema], operation_id="get_scan_sources")
@paginate(PageNumberPagination)
def get_all_sources(
    request: HttpRequest,  # noqa: ARG001
):
    return ImageSource.objects.all()


@router.get(
    "/{source_id}/",
    response=ImageSourceReadOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_single_scan_source",
)
async def get_single_source(
    request: HttpRequest,  # noqa: ARG001
    source_id: int,
):
    instance: ImageSource = await aget_object_or_404(ImageSource, id=source_id)
    return instance


@router.post(
    "/",
    response={HTTPStatus.CREATED: ImageSourceReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.CONFLICT: {
                "description": "Source already exists",
            },
        },
    },
    operation_id="create_scan_source",
)
async def create_source(
    request: HttpRequest,  # noqa: ARG001
    data: ImageSourceCreateInSchema,
):
    source_name_exists = await ImageSource.objects.filter(name__iexact=data.name).aexists()
    if source_name_exists:
        msg = f"Image source named {data.name} already exists"
        logger.error(msg)
        raise HttpConflictError(msg)

    instance: ImageSource = await ImageSource.objects.acreate(
        name=data.name,
        description=data.description,
    )
    return HTTPStatus.CREATED, instance


@router.patch(
    "/{source_id}/",
    response={HTTPStatus.OK: ImageSourceReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_scan_source",
)
async def update_source(
    request: HttpRequest,  # noqa: ARG001
    source_id: int,
    data: ImageSourceUpdateInSchema,
):
    # Retrieve the location object from the database
    instance: ImageSource = await aget_object_or_404(ImageSource, id=source_id)

    if data.name:
        instance.name = data.name
    instance.description = data.description

    await instance.asave()

    await instance.arefresh_from_db()
    return instance
