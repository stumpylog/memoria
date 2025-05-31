import logging
import tempfile
import zipfile
from http import HTTPStatus
from pathlib import Path

from django.db import transaction
from django.db.models import Case
from django.db.models import F
from django.db.models import IntegerField
from django.db.models import Max
from django.db.models import Prefetch
from django.db.models import When
from django.db.models.functions import Coalesce
from django.http import FileResponse
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from ninja import Router
from ninja.pagination import LimitOffsetPagination
from ninja.pagination import paginate

from memoria.common.auth import active_user_auth
from memoria.common.auth import async_active_user_auth
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
from memoria.routes.albums.schemas import AlbumWithImagesOutSchema

router = Router(tags=["albums"])
logger = logging.getLogger(__name__)

# Prefetch helper for images in album, sorted by sort_order
image_in_album_prefetch = Prefetch(
    "imageinalbum_set",
    queryset=ImageInAlbum.objects.select_related("image").order_by("sort_order"),
    to_attr="prefetched_imageinals",
)

# Helper to always prefetch group relations
group_prefetch = ("view_groups", "edit_groups")


@router.get(
    "/",
    response=list[AlbumBasicReadOutSchema],
    description="List albums viewable by the current user",
    operation_id="list_albums",
    auth=active_user_auth,
)
@paginate(LimitOffsetPagination)
def list_albums(request: HttpRequest, album_name: str | None = None):
    """
    List all albums viewable by the current user.
    Returns basic album information including image count and permission groups.
    """
    qs = Album.objects.permitted(request.user).with_image_count()
    if album_name is not None:
        qs = qs.filter(name__icontains=album_name)
    return qs


@router.get(
    "/{album_id}/",
    response=AlbumWithImagesOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Album not found or inaccessible",
            },
        },
    },
    description="Retrieve full details of a single album",
    operation_id="get_album",
    auth=active_user_auth,
)
def get_album(request: HttpRequest, album_id: int):
    """
    Retrieve a single album including its images and group permissions.
    Fails with 404 if the album is not viewable by the user.
    """
    qs = Album.objects.permitted(request.user).with_images().with_image_count().prefetch_related(*group_prefetch)
    return get_object_or_404(qs, id=album_id)


@router.post(
    "/",
    response={HTTPStatus.CREATED: AlbumBasicReadOutSchema},
    description="Create a new album with optional view/edit groups",
    operation_id="create_album",
    auth=async_active_user_auth,
)
async def create_album(request: HttpRequest, data: AlbumCreateInSchema):  # noqa: ARG001
    """
    Create a new album with optional view/edit groups.
    Only authenticated users may create albums.
    """
    album: Album = await Album.objects.acreate(name=data.name, description=data.description)
    if data.view_group_ids:
        await album.view_groups.aset(data.view_group_ids)
    if data.edit_group_ids:
        await album.edit_groups.aset(data.edit_group_ids)
    await album.arefresh_from_db()

    return await Album.objects.filter(id=album.pk).with_image_count().prefetch_related(*group_prefetch).afirst()


@router.patch(
    "/{album_id}/",
    response=AlbumBasicReadOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Album not found or inaccessible",
            },
        },
    },
    description="Update album name, description, and group permissions",
    operation_id="update_album",
    auth=async_active_user_auth,
)
async def update_album(request: HttpRequest, album_id: int, data: AlbumUpdateInSchema):
    """
    Update album metadata (name, description) and/or group permissions.
    Only editors can modify album details.
    """
    qs = Album.objects.editable_by(request.user)
    album: Album = await aget_object_or_404(qs, id=album_id)
    fields_to_update = []
    if data.name is not None:
        album.name = data.name
        fields_to_update.append("name")
    if data.description is not None:
        album.description = data.description
        fields_to_update.append("description")
    if fields_to_update:
        await album.asave(update_fields=fields_to_update)
    if data.view_group_ids is not None:
        await album.view_groups.aset(data.view_group_ids)
    if data.edit_group_ids is not None:
        await album.edit_groups.aset(data.edit_group_ids)
    await album.arefresh_from_db()
    return await Album.objects.filter(id=album.pk).with_image_count().prefetch_related(*group_prefetch).afirst()


@router.patch(
    "/{album_id}/images/",
    response=AlbumWithImagesOutSchema,
    operation_id="add_images_to_album",
    auth=active_user_auth,
)
def add_images_to_album(request: HttpRequest, album_id: int, data: AlbumAddImageInSchema):
    """Add images to an album maintaining order and avoiding duplicates."""
    # Get album with permission check
    qs = Album.objects.editable_by(request.user).prefetch_related(
        "images",
        image_in_album_prefetch,
        *group_prefetch,
    )
    album = get_object_or_404(qs, id=album_id)

    # Validate that all requested images exist and are accessible
    accessible_images = Image.objects.viewable_by(request.user).filter(
        id__in=data.image_ids,
    )

    if accessible_images.count() != len(data.image_ids):
        msg = "Some images were not found or are not accessible"
        logger.warning(msg)
        raise HttpBadRequestError(msg)

    # Get existing image IDs to avoid duplicates
    existing_image_ids = set(
        ImageInAlbum.objects.filter(album=album).values_list("image_id", flat=True),
    )

    # Filter out images already in the album while preserving order
    new_image_ids = [img_id for img_id in data.image_ids if img_id not in existing_image_ids]

    if not new_image_ids:
        logger.info(f"No new images to add to album {album_id}")
        # Return current album state
        return (
            Album.objects.editable_by(request.user)
            .with_images()
            .with_image_count()
            .prefetch_related(*group_prefetch)
            .get(id=album_id)
        )

    # Use transaction for atomicity
    with transaction.atomic():
        # Get max sort order within transaction to avoid race conditions

        max_order = ImageInAlbum.objects.filter(album=album).aggregate(
            max_order=Coalesce(Max("sort_order"), -1),
        )["max_order"]

        # Create ImageInAlbum objects in batch
        image_in_album_objects = []
        sort_order = max_order + 1

        # Maintain the order from data.image_ids
        for img_id in new_image_ids:
            image_in_album_objects.append(
                ImageInAlbum(
                    album=album,
                    image_id=img_id,
                    sort_order=sort_order,
                ),
            )
            sort_order += 1

        # Bulk create for better performance
        ImageInAlbum.objects.bulk_create(image_in_album_objects)

        logger.info(f"Added {len(image_in_album_objects)} images to album {album_id}")

    # Return updated album
    return (
        Album.objects.editable_by(request.user)
        .with_images()
        .with_image_count()
        .prefetch_related(*group_prefetch)
        .get(id=album_id)
    )


@router.delete(
    "/{album_id}/images/",
    response=AlbumWithImagesOutSchema,
    operation_id="remove_images_from_album",
    auth=active_user_auth,
)
def remove_images_from_album(request: HttpRequest, album_id: int, data: AlbumRemoveImageInSchema):
    """
    Remove images from an album.
    """
    # Get album with permission check
    qs = Album.objects.editable_by(request.user).prefetch_related("images", *group_prefetch)
    album = get_object_or_404(qs, id=album_id)

    # Get existing ImageInAlbum records to remove
    images_to_remove = ImageInAlbum.objects.filter(
        album=album,
        image_id__in=data.image_ids,
    )

    removed_count = images_to_remove.count()
    requested_count = len(data.image_ids)

    if removed_count == 0:
        logger.warning(f"No images from {data.image_ids} found in album {album_id}")
    elif removed_count < requested_count:
        removed_ids = set(images_to_remove.values_list("image_id", flat=True))
        missing_ids = [img_id for img_id in data.image_ids if img_id not in removed_ids]
        logger.warning(f"Images {missing_ids} not found in album {album_id}")

    # Remove in transaction for consistency
    with transaction.atomic():
        images_to_remove.delete()
        logger.info(f"Removed {removed_count} images from album {album_id}")

    # Return updated album
    return (
        Album.objects.editable_by(request.user)
        .with_images()
        .with_image_count()
        .prefetch_related(*group_prefetch)
        .get(id=album_id)
    )


@router.patch(
    "/{album_id}/sort/",
    response=AlbumWithImagesOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Album not found or inaccessible",
            },
            HTTPStatus.BAD_REQUEST: {
                "description": "Sorting list mismatch with album contents",
            },
        },
    },
    description="Reorder images in the album using a list of image IDs",
    operation_id="sort_album_images",
    auth=active_user_auth,
)
def sort_album_images(request: HttpRequest, album_id: int, data: AlbumSortUpdateInSchema):
    """
    Reorder images in an album based on the provided list of image IDs.
    The new list must exactly match the current contents. Requires edit permissions.
    """
    qs = Album.objects.editable_by(request.user)
    album = get_object_or_404(qs, id=album_id)
    existing_ids = list(ImageInAlbum.objects.filter(album=album).values_list("image_id", flat=True))

    if set(existing_ids) != set(data.sorting) or len(existing_ids) != len(data.sorting):
        msg = f"Album contains {len(existing_ids)} images, but {len(data.sorting)} provided."
        logger.error(msg)
        raise HttpBadRequestError(msg)

    # First, offset all sort_order values to avoid conflicts
    with transaction.atomic():
        max_sort = len(data.sorting)
        ImageInAlbum.objects.filter(album=album).update(
            sort_order=F("sort_order") + max_sort + 1000,
        )

        # Then apply the new sorting
        cases = [When(image_id=img_id, then=pos) for pos, img_id in enumerate(data.sorting)]
        ImageInAlbum.objects.filter(album=album, image_id__in=data.sorting).update(
            sort_order=Case(*cases, output_field=IntegerField()),
        )

    return (
        Album.objects.editable_by(request.user)
        .with_images()
        .with_image_count()
        .prefetch_related(*group_prefetch)
        .get(id=album_id)
    )


@router.delete(
    "/{album_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    operation_id="delete_album",
    auth=active_user_auth,
)
async def delete_album(request: HttpRequest, album_id: int):
    """
    Delete an album. Only editors can delete albums.
    """
    qs = Album.objects.editable_by(request.user)
    instance = await aget_object_or_404(qs, id=album_id)
    await instance.adelete()
    return HTTPStatus.NO_CONTENT, None


@router.get(
    "/{album_id}/download/",
    operation_id="download_album",
    auth=active_user_auth,
)
def download_album(request: HttpRequest, album_id: int, *, zip_originals: bool = False):
    """
    Download all images in an album as a ZIP archive.
    You can choose original or full-size paths. Requires view access.
    Note: File operations remain synchronous for streaming response.
    """
    qs = Album.objects.permitted(request.user).prefetch_related(image_in_album_prefetch, *group_prefetch)
    album = get_object_or_404(qs, id=album_id)
    if not album.prefetched_imageinals:
        msg = f"Album {album.name} has no images"
        logger.error(msg)
        raise HttpBadRequestError(msg)
    zip_name = slugify(album.name)
    zip_path = Path(tempfile.mkdtemp()) / f"{zip_name}.zip"
    with zipfile.ZipFile(zip_path, mode="w") as output_zip:
        for idx, iia in enumerate(album.prefetched_imageinals):
            path = iia.image.original_path if zip_originals else iia.image.full_size_path
            output_zip.write(path, arcname=f"{idx + 1:010}{Path(path).suffix}")
    return FileResponse(zip_path.open(mode="rb"), content_type="application/zip", as_attachment=True)
