import logging
from http import HTTPStatus
from mimetypes import guess_type

from django.db import transaction
from django.http import FileResponse
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import condition
from ninja import Router
from ninja.decorators import decorate_view
from ninja.pagination import PageNumberPagination
from ninja.pagination import paginate
from scansteward.common.constants import WEBP_CONTENT_TYPE
from scansteward.common.errors import HttpConflictError
from scansteward.models import Image
from scansteward.models import Person
from scansteward.models import PersonInImage
from scansteward.models import Pet
from scansteward.models import PetInImage
from scansteward.models import RoughDate
from scansteward.models import RoughLocation
from scansteward.models import Tag
from scansteward.models import TagOnImage
from scansteward.routes.images.common import get_faces_from_image
from scansteward.routes.images.common import get_image_metadata_common
from scansteward.routes.images.common import get_pet_boxes_from_image
from scansteward.routes.images.conditionals import full_size_etag
from scansteward.routes.images.conditionals import image_last_modified
from scansteward.routes.images.conditionals import original_image_etag
from scansteward.routes.images.conditionals import thumbnail_etag
from scansteward.routes.images.filters import CommaSepIntList
from scansteward.routes.images.schemas import ImageMetadataOutSchema
from scansteward.routes.images.schemas import ImageMetadataUpdateInSchema
from scansteward.routes.images.schemas import PersonFaceDeleteSchema
from scansteward.routes.images.schemas import PersonWithBoxSchema
from scansteward.routes.images.schemas import PetBoxDeleteInSchema
from scansteward.routes.images.schemas import PetWithBoxSchema

router = Router(tags=["images"])
logger = logging.getLogger(__name__)


@router.get("", response=list[int], operation_id="get_all_images")
@paginate(PageNumberPagination)
def get_all_images(
    request: HttpRequest,  # noqa: ARG001
    includes_people: CommaSepIntList | None = None,
    excludes_people: CommaSepIntList | None = None,
    includes_pets: CommaSepIntList | None = None,
    excludes_pets: CommaSepIntList | None = None,
    includes_locations: CommaSepIntList | None = None,
    excludes_locations: CommaSepIntList | None = None,
) -> list[int]:
    """
    Get all images, filtered as requested
    """
    qs = (
        Image.objects.all()
        .filter(deleted_at__isnull=True)
        .select_related("location")
        .prefetch_related("people", "pets")
    )

    if includes_people:
        qs = qs.filter(people__id__in=includes_people)
    if excludes_people:
        qs = qs.exclude(people__id__in=excludes_people)
    if includes_pets:
        qs = qs.filter(pets__id__in=includes_pets)
    if excludes_pets:
        qs = qs.exclude(pets__id__in=excludes_pets)
    if includes_locations:
        qs = qs.filter(location__id__in=includes_locations)
    if excludes_locations:
        qs = qs.exclude(location__id__in=excludes_locations)

    return qs.only("pk").all().values_list("pk", flat=True)


@router.get(
    "/{image_id}/thumbnail/",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.OK: {
                "content": {WEBP_CONTENT_TYPE: {"schema": {"type": "string", "format": "binary"}}},
            },
        },
    },
    operation_id="get_image_thumbnail",
)
@decorate_view(
    condition(last_modified_func=image_last_modified, etag_func=thumbnail_etag),
)
def get_image_thumbnail(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    img: Image = get_object_or_404(Image, id=image_id)

    return FileResponse(img.thumbnail_path.open(mode="rb"), content_type=WEBP_CONTENT_TYPE)


@router.get(
    "/{image_id}/full/",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.OK: {
                "content": {WEBP_CONTENT_TYPE: {"schema": {"type": "string", "format": "binary"}}},
            },
        },
    },
    operation_id="get_image_full_size",
)
@decorate_view(
    condition(last_modified_func=image_last_modified, etag_func=full_size_etag),
)
def get_image_full_size(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    img: Image = get_object_or_404(Image, id=image_id)

    return FileResponse(img.full_size_path.open(mode="rb"), content_type=WEBP_CONTENT_TYPE)


@router.get(
    "/{image_id}/original/",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.OK: {"content": {"image/*": {"schema": {"type": "string", "format": "binary"}}}},
        },
    },
    operation_id="get_image_original",
)
@decorate_view(
    condition(last_modified_func=image_last_modified, etag_func=original_image_etag),
)
def get_image_original(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    img: Image = get_object_or_404(Image, id=image_id)

    mimetype, _ = guess_type(img.original_path)
    if not mimetype:  # pragma: no cover
        mimetype = "image/jpeg"

    return FileResponse(img.original_path.open(mode="rb"), content_type=mimetype)


@router.delete(
    "/{image_id}/delete/",
    response={HTTPStatus.NO_CONTENT: None},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_image",
)
async def delete_image(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    img: Image = await aget_object_or_404(Image, id=image_id)

    img.deleted_at = timezone.now()

    await img.asave()

    return HTTPStatus.NO_CONTENT, None


@router.patch(
    "/{image_id}/restore/",
    response={HTTPStatus.NO_CONTENT: None},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.CONFLICT: {
                "description": "The image was not previously deleted",
            },
        },
    },
    operation_id="restore_image",
)
async def restore_image(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    img: Image = await aget_object_or_404(Image, id=image_id)

    if img.deleted_at is None:
        msg = f"Image {image_id} was not previously deleted"
        logger.warning(msg)
        raise HttpConflictError(msg)

    img.deleted_at = None

    await img.asave()

    return HTTPStatus.NO_CONTENT, None


@router.get(
    "/{image_id}/faces/",
    response={HTTPStatus.OK: list[PersonWithBoxSchema]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_faces_in_images",
)
async def get_faces_in_images(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    # TODO: I bet there's some clever SQL to grab this more efficiently

    img: Image = await aget_object_or_404(Image.objects.prefetch_related("people"), id=image_id)

    return await get_faces_from_image(img)


@router.patch(
    "/{image_id}/faces/",
    response={HTTPStatus.OK: list[PersonWithBoxSchema]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_faces_in_image",
)
async def update_faces_in_image(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
    data: list[PersonWithBoxSchema],
):
    img: Image = await aget_object_or_404(Image.objects.prefetch_related("people"), id=image_id)

    for update_item in data:
        person: Person = await img.people.aget(id=update_item.person_id)
        bounding_box: PersonInImage = await person.images.aget(image=img, person=person)
        bounding_box.center_x = update_item.box.center_x
        bounding_box.center_y = update_item.box.center_y
        bounding_box.height = update_item.box.height
        bounding_box.width = update_item.box.width
        await bounding_box.asave()

    return await get_faces_from_image(img)


@router.delete(
    "/{image_id}/faces/",
    response={HTTPStatus.OK: list[PersonWithBoxSchema]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_faces_in_image",
)
async def delete_faces_in_image(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
    data: PersonFaceDeleteSchema,
):
    img: Image = await aget_object_or_404(Image.objects.prefetch_related("people"), id=image_id)

    # TODO: transaction
    async for person in img.people.filter(pk__in=data.people_ids).all():
        await img.people.aremove(person)
    await img.arefresh_from_db()

    return await get_faces_from_image(img)


@router.get(
    "/{image_id}/pets/",
    response={HTTPStatus.OK: list[PetWithBoxSchema]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_pets_in_images",
)
async def get_pets_in_images(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    # TODO: I bet there's some clever SQL to grab this more efficiently

    img: Image = await aget_object_or_404(Image.objects.prefetch_related("pets"), id=image_id)

    return await get_pet_boxes_from_image(img)


@router.patch(
    "/{image_id}/pets/",
    response={HTTPStatus.OK: list[PetWithBoxSchema]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_pet_boxes_in_image",
)
async def update_pet_boxes_in_image(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
    data: list[PetWithBoxSchema],
):
    img: Image = await aget_object_or_404(Image.objects.prefetch_related("pets"), id=image_id)

    for update_item in data:
        pet: Pet = await img.pets.aget(id=update_item.pet_id)
        bounding_box: PetInImage = await pet.images.aget(image=img, pet=pet)
        bounding_box.center_x = update_item.box.center_x
        bounding_box.center_y = update_item.box.center_y
        bounding_box.height = update_item.box.height
        bounding_box.width = update_item.box.width
        await bounding_box.asave()

    return await get_pet_boxes_from_image(img)


@router.delete(
    "/{image_id}/pets/",
    response={HTTPStatus.OK: list[PetWithBoxSchema]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_pets_from_image",
)
async def delete_pets_from_image(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
    data: PetBoxDeleteInSchema,
):
    img: Image = await aget_object_or_404(Image.objects.prefetch_related("pets"), id=image_id)

    # TODO: transaction
    async for pet in img.pets.filter(pk__in=data.pet_ids).all():
        await img.pets.aremove(pet)
    await img.arefresh_from_db()

    return await get_pet_boxes_from_image(img)


@router.get(
    "/{image_id}/metadata/",
    response={HTTPStatus.OK: ImageMetadataOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_image_metadata",
)
async def get_image_metadata(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    # TODO: I bet there's some clever SQL to grab this more efficiently

    img: Image = await aget_object_or_404(
        Image.objects.select_related("location").select_related("date"),
        id=image_id,
    )

    return await get_image_metadata_common(img)


@router.patch(
    "/{image_id}/metadata/",
    response={HTTPStatus.OK: ImageMetadataOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_image_metadata",
)
async def update_image_metadata(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
    data: ImageMetadataUpdateInSchema,
):
    img: Image = await aget_object_or_404(
        Image.objects.select_related("location").select_related("date"),
        id=image_id,
    )

    if data.orientation is not None:
        img.orientation = data.orientation
    if data.description is not None:
        img.description = data.description
    if data.location_id is not None:
        img.location = await aget_object_or_404(RoughLocation, pk=data.location_id)
    if data.date_id is not None:
        img.date = await aget_object_or_404(RoughDate, pk=data.date_id)

    await img.asave()

    return await get_image_metadata_common(img)


@router.get(
    "/{image_id}/albums/",
    response={HTTPStatus.OK: list[int]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_image_albums",
)
async def get_image_albums(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    img: Image = await aget_object_or_404(Image.objects.prefetch_related("albums"), id=image_id)
    return [pk async for pk in img.albums.all().only("pk").values_list("pk", flat=True)]


@router.get(
    "/{image_id}/tags/",
    response={HTTPStatus.OK: list[int]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_image_tags",
)
async def get_image_tags(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
):
    img: Image = await aget_object_or_404(Image.objects.prefetch_related("tags"), id=image_id)
    return [
        pk
        async for pk in Tag.objects.filter(tagonimage__image=img, tagonimage__applied=True)
        .only("pk")
        .values_list("pk", flat=True)
    ]


@router.patch(
    "/{image_id}/tags/",
    response={HTTPStatus.OK: list[int]},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_image_tags",
)
def update_image_tags(
    request: HttpRequest,  # noqa: ARG001
    image_id: int,
    new_tag_ids: list[int],
):
    img: Image = get_object_or_404(Image.objects.prefetch_related("tags"), id=image_id)

    with transaction.atomic():
        # 1. Remove existing TagOnImage entries not in the new list
        TagOnImage.objects.filter(image=img).exclude(tag_id__in=new_tag_ids).delete()

        # 2. Update existing TagOnImage entries or create new ones
        existing_links = TagOnImage.objects.filter(image=img, tag_id__in=new_tag_ids)

        existing_tag_ids = set(existing_links.values_list("tag_id", flat=True))

        for tag_id in new_tag_ids:
            if tag_id in existing_tag_ids:
                # If the link exists, update the applied field to True
                existing_links.filter(tag_id=tag_id).update(applied=True)
            else:
                # If the link does not exist, create it with applied=True
                TagOnImage.objects.create(image=img, tag_id=tag_id, applied=True)

    return list(
        Tag.objects.filter(tagonimage__image=img, tagonimage__applied=True).only("pk").values_list("pk", flat=True),
    )
