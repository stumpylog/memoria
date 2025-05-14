import logging
import tempfile
import zipfile
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import Max
from django.http import FileResponse
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from ninja import Router
from ninja.pagination import PageNumberPagination
from ninja.pagination import paginate

from memoria.common.errors import HttpBadRequestError
from memoria.models import Album
from memoria.models import Image
from memoria.models import ImageInAlbum
from memoria.routes.albums.schemas import AlbumAddImageInSchema
from memoria.routes.albums.schemas import AlbumBasicReadOutSchema
from memoria.routes.albums.schemas import AlbumCreateInSchema
from memoria.routes.albums.schemas import AlbumRemoveImageInSchema
from memoria.routes.albums.schemas import AlbumSortUpdateInSchema
from memoria.routes.albums.schemas import AlbumUpdateInSchema
from memoria.routes.albums.schemas import AlbumWithImagesReadInSchema

router = Router(tags=["albums"])

logger = logging.getLogger(__name__)


@router.get("/", response=list[AlbumBasicReadOutSchema], operation_id="get_albums")
@paginate(PageNumberPagination)
def get_albums(
    request: HttpRequest,  # noqa: ARG001
    name_like: str | None = None,
):
    qs = Album.objects.all()
    if name_like is not None:
        qs = qs.filter(name__icontains=name_like)

    return qs


@router.get(
    "/{album_id}/",
    response=AlbumWithImagesReadInSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_single_album_info",
)
def get_album(
    request: HttpRequest,  # noqa: ARG001
    album_id: int,
):
    album_instance: Album = get_object_or_404(Album.objects.prefetch_related("images"), id=album_id)

    return album_instance


@router.post("/", response={HTTPStatus.CREATED: AlbumBasicReadOutSchema}, operation_id="create_album")
async def create_album(
    request: HttpRequest,  # noqa: ARG001
    data: AlbumCreateInSchema,
):
    instance: Album = await Album.objects.acreate(
        name=data.name,
        description=data.description,
    )
    return HTTPStatus.CREATED, instance


@router.patch(
    "/{album_id}/",
    response=AlbumBasicReadOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_album_info",
)
async def update_album(
    request: HttpRequest,  # noqa: ARG001
    album_id: int,
    data: AlbumUpdateInSchema,
):
    instance: Album = await aget_object_or_404(Album, id=album_id)
    if data.name is not None:
        instance.name = data.name
    instance.description = data.description
    await instance.asave()
    await instance.arefresh_from_db()
    return instance


@router.patch(
    "/{album_id}/add/",
    response=AlbumWithImagesReadInSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="add_image_to_album",
)
def add_image_to_album(
    request: HttpRequest,  # noqa: ARG001
    album_id: int,
    data: AlbumAddImageInSchema,
):
    album_instance: Album = get_object_or_404(Album.objects.prefetch_related("images"), id=album_id)

    sort_order = (
        ImageInAlbum.objects.filter(album=album_instance).aggregate(Max("sort_order", default=0))["sort_order__max"] + 1
    )

    for image in Image.objects.filter(id__in=data.image_ids).all():
        _ = ImageInAlbum.objects.get_or_create(
            album=album_instance,
            image=image,
            sort_order=sort_order,
        )
        sort_order += 1
    album_instance.refresh_from_db()

    return album_instance


@router.patch(
    "/{album_id}/remove/",
    response=AlbumWithImagesReadInSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_image_from_album",
)
def remove_image_from_album(
    request: HttpRequest,  # noqa: ARG001
    album_id: int,
    data: AlbumRemoveImageInSchema,
):
    album_instance: Album = get_object_or_404(Album.objects.prefetch_related("images"), id=album_id)

    for image in Image.objects.filter(id__in=data.image_ids).all():
        if album_instance.images.filter(pk=image.pk).exists():
            album_instance.images.remove(image)
        else:
            logger.warning(f"Image {image.pk} not in album {album_instance.pk}")

    album_instance.refresh_from_db()

    return album_instance


@router.patch(
    "/{album_id}/sort/",
    response=AlbumWithImagesReadInSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.BAD_REQUEST: {
                "description": "Sorting data did not match album image count",
            },
        },
    },
    operation_id="update_album_sorting",
)
def update_album_sorting(
    request: HttpRequest,  # noqa: ARG001
    album_id: int,
    data: AlbumSortUpdateInSchema,
):
    album_instance: Album = get_object_or_404(Album.objects.prefetch_related("images"), id=album_id)

    if album_instance.images.count() != len(data.sorting):
        msg = f"Album contains {album_instance.images.count()} images, "
        f"but {len(data.sorting)} sorting values were provided."
        logger.error(msg)
        raise HttpBadRequestError(msg)

    with transaction.atomic():
        # For a moment, reset the sorting order to be above the current largest
        temp_sort_order = (
            ImageInAlbum.objects.filter(album=album_instance).aggregate(Max("sort_order", default=0))["sort_order__max"]
            + 1
        )
        for image_in_album_instance in ImageInAlbum.objects.filter(album=album_instance).all():
            image_in_album_instance.sort_order = temp_sort_order
            image_in_album_instance.save()
            temp_sort_order += 1

        for index, image_id in enumerate(data.sorting):
            image_instance = get_object_or_404(Image, id=image_id)
            image_in_album_instance = get_object_or_404(
                ImageInAlbum,
                album=album_instance,
                image=image_instance,
            )
            image_in_album_instance.sort_order = index
            image_in_album_instance.save()

    album_instance.refresh_from_db()

    return album_instance


@router.delete(
    "/{album_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_album",
)
async def delete_album(
    request: HttpRequest,  # noqa: ARG001
    album_id: int,
):
    instance: Album = await aget_object_or_404(Album, id=album_id)
    await instance.adelete()
    return HTTPStatus.NO_CONTENT, None


@router.get(
    "/{album_id}/download/",
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.BAD_REQUEST: {
                "description": "No images in album",
            },
            HTTPStatus.OK: {
                "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}},
            },
        },
    },
    operation_id="download_album",
)
def download_album(
    request: HttpRequest,  # noqa: ARG001
    album_id: int,
    *,
    zip_originals: bool = False,
):
    album_instance: Album = get_object_or_404(Album.objects.prefetch_related("images"), id=album_id)

    if album_instance.images.count() == 0:
        msg = f"Album {album_instance.name} has no images"
        logger.error(msg)
        raise HttpBadRequestError(msg)

    zip_name = slugify(album_instance.name)
    # TODO: Track and clean these up on a schedule?
    zip_path = Path(tempfile.mkdtemp()) / f"{zip_name}.zip"
    with zipfile.ZipFile(zip_path, mode="w") as output_zip:
        for index, image in enumerate(album_instance.images.order_by("imageinalbum__sort_order").all()):
            if TYPE_CHECKING:
                assert isinstance(image, Image)
            if zip_originals:
                output_zip.write(image.original_path, arcname=f"{index + 1:010}{image.original_path.suffix}")
            else:
                output_zip.write(
                    image.full_size_path,
                    arcname=f"{index + 1:010}{image.full_size_path.suffix}",
                )

    return FileResponse(zip_path.open(mode="rb"), content_type="application/zip", as_attachment=True)
