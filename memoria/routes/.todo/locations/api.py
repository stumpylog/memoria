import logging
from http import HTTPStatus

from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Router
from ninja.pagination import PageNumberPagination
from ninja.pagination import paginate
from scansteward.common.errors import HttpBadRequestError
from scansteward.common.errors import HttpConflictError
from scansteward.models import RoughLocation
from scansteward.routes.locations.schemas import LocationCreateInSchema
from scansteward.routes.locations.schemas import LocationReadOutSchema
from scansteward.routes.locations.schemas import LocationUpdateInSchema
from scansteward.routes.locations.utils import subdivision_in_country
from simpleiso3166.countries.types import CountryCodeAlpha2Type
from simpleiso3166.subdivisions.types import SubdivisionCodeType

router = Router(tags=["locations"])

logger = logging.getLogger(__name__)


@router.get("/", response=list[LocationReadOutSchema], operation_id="get_locations")
@paginate(PageNumberPagination)
def get_all_locations(
    request: HttpRequest,  # noqa: ARG001
    country_code: CountryCodeAlpha2Type | None = None,
    subdivision_code: SubdivisionCodeType | None = None,
    city_like: str | None = None,
    shown_location_like: str | None = None,
):
    qs = RoughLocation.objects.all()
    if country_code is not None:
        qs = qs.filter(country_code=country_code)
    if subdivision_code is not None:
        qs = qs.filter(subdivision_code=subdivision_code)
    if city_like:
        qs = qs.filter(city__icontains=city_like)
    if shown_location_like:
        qs = qs.filter(sub_location__icontains=shown_location_like)
    return qs


@router.get(
    "/{location_id}/",
    response=LocationReadOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_location",
)
async def get_single_location(
    request: HttpRequest,  # noqa: ARG001
    location_id: int,
):
    instance: RoughLocation = await aget_object_or_404(RoughLocation, id=location_id)
    return instance


@router.post(
    "/",
    response={HTTPStatus.CREATED: LocationReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.BAD_REQUEST: {
                "description": "Subdivision provided without country",
            },
            HTTPStatus.CONFLICT: {
                "description": "RoughLocation already exists",
            },
        },
    },
    operation_id="create_location",
)
async def create_location(
    request: HttpRequest,  # noqa: ARG001
    data: LocationCreateInSchema,
):
    if data.subdivision_code and not subdivision_in_country(
        data.country_code,
        data.subdivision_code,
    ):
        msg = f"Subdivision {data.subdivision_code} is not in country {data.country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)

    instance, created = await RoughLocation.objects.aget_or_create(
        country_code=data.country_code,
        subdivision_code=data.subdivision_code,
        city=data.city,
        sub_location=data.sub_location,
    )
    if not created:
        msg = "RoughLocation with provided fields already exists"
        logger.error(msg)
        raise HttpConflictError(msg)

    return HTTPStatus.CREATED, instance


@router.patch(
    "/{location_id}/",
    response={HTTPStatus.OK: LocationReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_location",
)
async def update_location(
    request: HttpRequest,  # noqa: ARG001
    location_id: int,
    data: LocationUpdateInSchema,
):
    # Validate that at least one field is provided to be updated
    if not any([data.country_code, data.subdivision_code, data.city, data.sub_location]):
        msg = "At least one of the fields must be provided"
        logger.error(msg)
        raise HttpBadRequestError(msg)

    # Retrieve the location object from the database
    instance: RoughLocation = await aget_object_or_404(RoughLocation, id=location_id)

    # Update the country
    if data.country_code:
        instance.country_code = str(data.country_code)

    # Update the subdivision/state/province value
    if data.subdivision_code:
        instance.subdivision_code = data.subdivision_code

    instance.city = data.city
    instance.sub_location = data.sub_location

    await instance.asave()
    await instance.arefresh_from_db()
    return instance


@router.delete(
    "/{location_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_location",
)
async def delete_location(
    request: HttpRequest,  # noqa: ARG001
    location_id: int,
):
    instance: RoughLocation = await aget_object_or_404(RoughLocation, id=location_id)
    await instance.adelete()
    return HTTPStatus.NO_CONTENT, None
