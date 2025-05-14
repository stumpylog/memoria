import logging
import tempfile
import zipfile
from http import HTTPStatus
from pathlib import Path

from django.db.models import Case
from django.db.models import IntegerField
from django.db.models import Max
from django.db.models import Prefetch
from django.db.models import When
from django.http import FileResponse
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from ninja import Router

from memoria.common.auth import active_user_auth
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
    operation_id="get_albums",
    auth=active_user_auth,
)
def get_albums(request: HttpRequest):
    """
    List all albums viewable by the current user.
    Returns basic album information including image count and permission groups.
    """
    return Album.objects.permitted(request.user).with_image_count().prefetch_related(*group_prefetch)


@router.get(
    "/{album_id}/",
    response=AlbumWithImagesReadInSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Album not found or inaccessible",
            },
        },
    },
    description="Retrieve full details of a single album",
    operation_id="get_single_album_info",
    auth=active_user_auth,
)
def get_album(request: HttpRequest, album_id: int):
    """
    Retrieve a single album including its images and group permissions.
    Fails with 404 if the album is not viewable by the user.
    """
    qs = Album.objects.permitted(request.user).with_images().prefetch_related(*group_prefetch)
    return get_object_or_404(qs, id=album_id)


@router.post(
    "/",
    response={HTTPStatus.CREATED: AlbumBasicReadOutSchema},
    description="Create a new album with optional view/edit groups",
    operation_id="create_album",
    auth=active_user_auth,
)
async def create_album(request: HttpRequest, data: AlbumCreateInSchema):
    """
    Create a new album with optional view/edit groups.
    Only authenticated users may create albums.
    """
    album = await Album.objects.acreate(name=data.name, description=data.description)
    if data.view_group_ids:
        await album.view_groups.aset(data.view_group_ids)
    if data.edit_group_ids:
        await album.edit_groups.aset(data.edit_group_ids)
    await album.arefresh_from_db()
    return HTTPStatus.CREATED, (
        Album.objects.filter(id=album.id).with_image_count().prefetch_related(*group_prefetch).first()
    )


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
    operation_id="update_album_info",
    auth=active_user_auth,
)
async def update_album(request: HttpRequest, album_id: int, data: AlbumUpdateInSchema):
    """
    Update album metadata (name, description) and/or group permissions.
    Only editors can modify album details.
    """
    qs = Album.objects.editable_by(request.user)
    album = await aget_object_or_404(qs, id=album_id)
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
    return Album.objects.filter(id=album.id).with_image_count().prefetch_related(*group_prefetch).first()


@router.patch(
    "/{album_id}/add/",
    response=AlbumWithImagesReadInSchema,
    operation_id="add_image_to_album",
    auth=active_user_auth,
)
def add_image_to_album(request: HttpRequest, album_id: int, data: AlbumAddImageInSchema):
    qs = Album.objects.editable_by(request.user).prefetch_related("images", image_in_album_prefetch, *group_prefetch)
    album = get_object_or_404(qs, id=album_id)
    max_order = ImageInAlbum.objects.filter(album=album).aggregate(max_order=Max("sort_order"))["max_order"] or -1
    sort_order = max_order + 1
    for img in Image.objects.filter(id__in=data.image_ids):
        ImageInAlbum.objects.get_or_create(album=album, image=img, defaults={"sort_order": sort_order})
        sort_order += 1
    return Album.objects.editable_by(request.user).with_images().prefetch_related(*group_prefetch).get(id=album_id)


@router.patch(
    "/{album_id}/remove/",
    response=AlbumWithImagesReadInSchema,
    operation_id="delete_image_from_album",
    auth=active_user_auth,
)
def remove_image_from_album(request: HttpRequest, album_id: int, data: AlbumRemoveImageInSchema):
    qs = Album.objects.editable_by(request.user).prefetch_related("images", *group_prefetch)
    album = get_object_or_404(qs, id=album_id)
    for img in Image.objects.filter(id__in=data.image_ids):
        if album.images.filter(pk=img.pk).exists():
            album.images.remove(img)
        else:
            logger.warning(f"Image {img.pk} not in album {album.pk}")
    return Album.objects.editable_by(request.user).with_images().prefetch_related(*group_prefetch).get(id=album_id)


@router.patch(
    "/{album_id}/sort/",
    response=AlbumWithImagesReadInSchema,
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
    operation_id="update_album_sorting",
    auth=active_user_auth,
)
def update_album_sorting(request: HttpRequest, album_id: int, data: AlbumSortUpdateInSchema):
    """
    Reorder images in an album based on the provided list of image IDs.
    The new list must exactly match the current contents. Requires edit permissions.
    """
    # Efficient single-query reordering using Case/When
    qs = Album.objects.editable_by(request.user)
    album = get_object_or_404(qs, id=album_id)

    existing_ids = list(ImageInAlbum.objects.filter(album=album).values_list("image_id", flat=True))
    if set(existing_ids) != set(data.sorting) or len(existing_ids) != len(data.sorting):
        msg = f"Album contains {len(existing_ids)} images, but {len(data.sorting)} provided."
        logger.error(msg)
        raise HttpBadRequestError(msg)

    # Build CASE expressions
    cases = [When(image_id=img_id, then=pos) for pos, img_id in enumerate(data.sorting)]
    ImageInAlbum.objects.filter(album=album, image_id__in=data.sorting).update(
        sort_order=Case(*cases, output_field=IntegerField()),
    )

    return Album.objects.editable_by(request.user).with_images().prefetch_related(*group_prefetch).get(id=album_id)


@router.delete(
    "/{album_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    operation_id="delete_album",
    auth=active_user_auth,
)
async def delete_album(request: HttpRequest, album_id: int):
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
