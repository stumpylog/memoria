import logging
from datetime import date
from http import HTTPStatus
from typing import Literal
from typing import cast

from django.contrib.auth import get_user_model
from django.db.models import BooleanField
from django.db.models import Case
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Value
from django.db.models import When
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router
from ninja.pagination import LimitOffsetPagination
from ninja.pagination import paginate
from simpleiso3166 import Country
from simpleiso3166 import CountryCodeAlpha2Type

from memoria.common.auth import active_user_auth
from memoria.common.errors import HttpBadRequestError
from memoria.models import Image
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.routes.images.filters import ImageBooleanFilterSchema
from memoria.routes.images.filters import ImageDateFilterSchema
from memoria.routes.images.filters import ImageExactDateFilterSchema
from memoria.routes.images.filters import ImageFKFilterSchema
from memoria.routes.images.filters import ImageLocationFilterSchema
from memoria.routes.images.filters import ImageM2MFilterSchema
from memoria.routes.images.schemas import ImageDateSchemaOut
from memoria.routes.images.schemas import ImageDateUpdateSchemaIn
from memoria.routes.images.schemas import ImageLocationSchemaOut
from memoria.routes.images.schemas import ImageLocationUpdateSchemaIn
from memoria.routes.images.schemas import ImageMetadataSchemaOut
from memoria.routes.images.schemas import ImageMetadataUpdateSchemaIn
from memoria.routes.images.schemas import ImageThumbnailSchemaOut
from memoria.routes.images.schemas import PersonInImageSchemaOut
from memoria.routes.images.schemas import PetInImageSchemaOut

router = Router(tags=["images"])
logger = logging.getLogger(__name__)
UserModelT = get_user_model()


def get_annotated_image_queryset(user: UserModelT):
    return (
        Image.objects.permitted(user)
        .with_folder()
        .annotate(
            # Permission-based fields
            can_edit=Case(
                When(Value(user.is_superuser), then=Value(True)),
                default=Exists(
                    user.groups.filter(id__in=OuterRef("edit_groups")),
                ),
                output_field=BooleanField(),
            ),
        )
    )


@router.get("/", response=list[ImageThumbnailSchemaOut], auth=active_user_auth, operation_id="list_images")
@paginate(LimitOffsetPagination)
def list_images(
    request: HttpRequest,
    boolean_filters: ImageBooleanFilterSchema = Query(...),
    fk_filters: ImageFKFilterSchema = Query(...),
    m2m_filters: ImageM2MFilterSchema = Query(...),
    date_range_filters: ImageDateFilterSchema = Query(...),
    date_exact_filters: ImageExactDateFilterSchema = Query(...),
    location_filters: ImageLocationFilterSchema = Query(...),
    sort_by: Literal["created_at", "-created_at", "updated_at", "-updated_at", "pk", "title", "-title"] = Query(
        "pk",
        description="Field to sort by",
    ),
):
    qs = (
        Image.objects.permitted(request.user)
        .with_date()
        .with_folder()
        .with_location()
        .with_people()
        .with_pets()
        .with_tags()
    )

    qs = Image.objects.permitted(request.user)
    qs = boolean_filters.filter_queryset(qs)
    qs = fk_filters.filter_queryset(qs)
    qs = m2m_filters.filter_queryset(qs)
    qs = date_range_filters.filter_queryset(qs)
    qs = date_exact_filters.filter_queryset(qs)
    return location_filters.filter_queryset(qs).order_by(sort_by)


@router.get(
    "/{image_id}/thumbnail/",
    response=ImageThumbnailSchemaOut,
    auth=active_user_auth,
    operation_id="image_get_thumb_info",
)
def get_image_thumbnail_info(request: HttpRequest, image_id: int):
    return get_object_or_404(Image.objects.permitted(request.user), pk=image_id)


@router.post(
    "/bulk/thumbnails/",
    response=list[ImageThumbnailSchemaOut],
    auth=active_user_auth,
    operation_id="image_get_thumbnails_bulk_info",
)
def get_image_thumbnails_bulk_info(request: HttpRequest, image_ids: list[int]):
    return Image.objects.permitted(request.user).filter(pk__in=image_ids)


@router.get(
    "/{image_id}/metadata/",
    response=ImageMetadataSchemaOut,
    auth=active_user_auth,
    operation_id="image_get_metadata",
)
def get_image_details(request: HttpRequest, image_id: int):
    return get_object_or_404(get_annotated_image_queryset(request.user), pk=image_id)


@router.get(
    "/{image_id}/date/",
    response={HTTPStatus.OK: ImageDateSchemaOut, HTTPStatus.NO_CONTENT: None},
    auth=active_user_auth,
    operation_id="image_get_date",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "The image does not exist",
            },
            HTTPStatus.NO_CONTENT: {
                "description": "The image has no date",
            },
            HTTPStatus.UNAUTHORIZED: {
                "description": "The user does not have permissions for this image",
            },
        },
    },
)
def get_image_date(request: HttpRequest, image_id: int):
    img = get_object_or_404(Image.objects.permitted(request.user).with_date(), pk=image_id)
    if img.date is None:
        return HTTPStatus.NO_CONTENT, None
    return img.date


@router.get(
    "/{image_id}/location/",
    response={HTTPStatus.OK: ImageLocationSchemaOut, HTTPStatus.NO_CONTENT: None},
    auth=active_user_auth,
    operation_id="image_get_location",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "The image does not exist",
            },
            HTTPStatus.NO_CONTENT: {
                "description": "The image has no location",
            },
            HTTPStatus.UNAUTHORIZED: {
                "description": "The user does not have permissions for this image",
            },
        },
    },
)
def get_image_location(request: HttpRequest, image_id: int):
    img = get_object_or_404(Image.objects.permitted(request.user).with_location(), pk=image_id)
    if img.location is None:
        return HTTPStatus.NO_CONTENT, None
    return img.location


@router.get(
    "/{image_id}/people/",
    response=list[PersonInImageSchemaOut],
    auth=active_user_auth,
    operation_id="image_get_people",
)
def get_image_people(request: HttpRequest, image_id: int):
    img = get_object_or_404(Image.objects.permitted(request.user).with_people(), pk=image_id)
    return img.personinimage_set.all()


@router.get(
    "/{image_id}/pets/",
    response=list[PetInImageSchemaOut],
    auth=active_user_auth,
    operation_id="image_get_pets",
)
def get_image_pets(request: HttpRequest, image_id: int):
    img = get_object_or_404(Image.objects.permitted(request.user).with_pets(), pk=image_id)
    return img.petinimage_set.all()


@router.patch(
    "/{image_id}/metadata/",
    response=ImageMetadataSchemaOut,
    auth=active_user_auth,
    operation_id="image_update_metadata",
)
def update_image_details(request: HttpRequest, image_id: int, data: ImageMetadataUpdateSchemaIn):
    img: Image = get_object_or_404(Image.objects.editable_by(request.user), pk=image_id)
    if data.title is not None:
        img.title = data.title
    if data.description is not None:
        img.description = data.description
    img.save()

    # Refresh the image with annotations for the response
    return get_object_or_404(get_annotated_image_queryset(request.user), pk=image_id)


@router.patch(
    "/{image_id}/location/",
    response={HTTPStatus.OK: ImageLocationSchemaOut},
    auth=active_user_auth,
    operation_id="image_update_location",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "The image does not exist",
            },
            HTTPStatus.BAD_REQUEST: {
                "description": "The country is not found or subdivision is not in the country",
            },
            HTTPStatus.UNAUTHORIZED: {
                "description": "The user does not have permissions for this image",
            },
        },
    },
)
def update_image_location(request: HttpRequest, image_id: int, data: ImageLocationUpdateSchemaIn):
    img = get_object_or_404(Image.objects.editable_by(request.user), pk=image_id)

    country = Country.from_alpha2(cast("CountryCodeAlpha2Type", data.country_code))
    if not country:
        msg = f"The country code {data.country_code} is not a valid ISO-3166 alpha2 code"
        logger.warning(msg)
        raise HttpBadRequestError(msg)
    if data.subdivision_code and not country.contains_subdivision(data.subdivision_code):
        msg = f"The country {data.country_code} does not have the subdivision {data.subdivision_code}"
        logger.warning(msg)
        raise HttpBadRequestError(msg)
    if data.city:
        data.city = data.city.strip()
    if data.sub_location:
        data.sub_location = data.sub_location.strip()

    new_location, created = RoughLocation.objects.get_or_create(
        country_code=data.country_code,
        subdivision_code=data.subdivision_code,
        city=data.city,
        sub_location=data.sub_location,
    )

    if created:
        logger.info(f"Created new location: {new_location}")
    img.location = new_location
    img.save()

    return new_location


@router.patch(
    "/{image_id}/date/",
    response={HTTPStatus.OK: ImageDateSchemaOut},
    auth=active_user_auth,
    operation_id="image_update_date",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "The image does not exist",
            },
            HTTPStatus.UNAUTHORIZED: {
                "description": "The user does not have permissions for this image",
            },
        },
    },
)
def update_image_date(request: HttpRequest, image_id: int, data: ImageDateUpdateSchemaIn):
    img = get_object_or_404(Image.objects.editable_by(request.user), pk=image_id)
    new_date, created = RoughDate.objects.get_or_create(
        year=data.date.year,
        month=data.date.month if data.month_valid else None,
        day=data.date.day if data.day_valid else None,
        date=date(data.date.year, data.date.month if data.month_valid else 1, data.date.day if data.day_valid else 1),
    )

    if created:
        logger.info(f"Created new date: {new_date}")

    img.date = new_date
    img.save()

    return new_date
