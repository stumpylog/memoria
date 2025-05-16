import logging
from http import HTTPStatus
from typing import cast

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from simpleiso3166 import Country
from simpleiso3166 import CountryCodeAlpha2Type

from memoria.common.auth import active_user_auth
from memoria.common.errors import HttpBadRequestError
from memoria.models import Image
from memoria.models import RoughDate
from memoria.models import RoughLocation
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


@router.get(
    "/{image_id}/thumbnail/",
    response=ImageThumbnailSchemaOut,
    auth=active_user_auth,
    operation_id="image_get_thumb_info",
)
def get_image_thumbnail_info(request: HttpRequest, image_id: int):
    img = get_object_or_404(Image.objects.permitted(request.user), pk=image_id)
    return {
        "id": img.id,
        "title": img.title,
        "thumbnail_width": img.thumbnail_width,
        "thumbnail_height": img.thumbnail_height,
        "thumbnail_url": request.build_absolute_uri(img.thumbnail_url),
    }


@router.get(
    "/{image_id}/metadata/",
    response=ImageMetadataSchemaOut,
    auth=active_user_auth,
    operation_id="image_get_metadata",
)
def get_image_details(request: HttpRequest, image_id: int):
    img: Image = get_object_or_404(Image.objects.permitted(request.user), pk=image_id)
    return {
        "id": img.id,
        "orientation": img.orientation,
        "original_height": img.original_height,
        "original_width": img.original_width,
        "title": img.title,
        "file_size": img.file_size,
        "description": img.description,
        "created_at": img.created_at,
        "updated_at": img.updated_at,
        "original_checksum": img.original_checksum,
        "phash": img.phash,
        "original_path": img.original_path,
        "image_fs_id": img.image_fs_id,
        "larger_size_url": request.build_absolute_uri(img.larger_size_url),
        "can_edit": request.user.groups.filter(id__in=img.edit_groups.all()).exists() or request.user.is_superuser,
    }


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
    return {
        "id": img.id,
        "orientation": img.orientation,
        "original_height": img.original_height,
        "original_width": img.original_width,
        "title": img.title,
        "file_size": img.file_size,
        "description": img.description,
        "created_at": img.created_at,
        "updated_at": img.updated_at,
        "original_checksum": img.original_checksum,
        "phash": img.phash,
        "original_path": img.original_path,
        "image_fs_id": img.image_fs_id,
        "larger_size_url": request.build_absolute_uri(img.larger_size_url),
        "can_edit": request.user.groups.filter(id__in=img.edit_groups.all()).exists() or request.user.is_superuser,
    }


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
        raise HttpBadRequestError(f"The country code {data.country_code} is not a valid ISO-3166 alpha2 code")
    if data.subdivision_code and not country.contains_subdivision(data.subdivision_code):
        raise HttpBadRequestError(
            f"The country {data.country_code} does not have the subdivision {data.subdivision_code}",
        )
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
        date=data.date,
        month_valid=data.month_valid,
        day_valid=data.day_valid,
    )

    if created:
        logger.info(f"Created new date: {new_date}")

    img.date = new_date
    img.save()

    return new_date
