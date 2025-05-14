import logging
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from memoria.common.auth import active_user_auth
from memoria.models import Image
from memoria.routes.images.schemas import ImageDateSchema
from memoria.routes.images.schemas import ImageLocationSchema
from memoria.routes.images.schemas import ImageMetadataSchema
from memoria.routes.images.schemas import ImageThumbnailSchema
from memoria.routes.images.schemas import PersonInImageSchemaOut
from memoria.routes.images.schemas import PetInImageSchemaOut

router = Router(tags=["images"])
logger = logging.getLogger(__name__)
UserModelT = get_user_model()


@router.get(
    "/{image_id}/thumbnail/",
    response=ImageThumbnailSchema,
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
    response=ImageMetadataSchema,
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
        "full_size_url": request.build_absolute_uri(img.full_size_url),
    }


@router.get(
    "/{image_id}/date/",
    response={HTTPStatus.OK: ImageDateSchema, HTTPStatus.NO_CONTENT: None},
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
    response={HTTPStatus.OK: ImageLocationSchema, HTTPStatus.NO_CONTENT: None},
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
