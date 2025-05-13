import logging

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from ninja import Router

from memoria.common.errors import HttpNotAuthorizedError
from memoria.models import Image
from memoria.models import ImageFolder
from memoria.routes.folders.schemas import ImageFolderDetailSchema
from memoria.routes.folders.schemas import ImageFolderSchema

router = Router(tags=["folders"])
logger = logging.getLogger(__name__)
UserModelT = get_user_model()


def get_permission_filter(user: UserModelT):
    """
    Generate permission filter based on user groups
    """
    if user.is_superuser:
        return Q()
    groups = user.groups.all()
    return Q(view_groups__in=groups) | Q(edit_groups__in=groups)


def annotate_folder_counts(queryset, perm_filter):
    """Annotate folders with child and image counts"""
    # Subquery for direct child folders with permission check
    children_qs = (
        ImageFolder.objects.filter(
            Q(tn_parent=OuterRef("pk")) & perm_filter,
        )
        .values("tn_parent")
        .annotate(count=Count("pk", distinct=True))
        .values("count")
    )

    # Subquery for direct images with permission check
    image_qs = (
        Image.objects.filter(
            Q(folder=OuterRef("pk")) & perm_filter,
        )
        .values("folder")
        .annotate(count=Count("pk", distinct=True))
        .values("count")
    )

    # Annotate counts
    return queryset.annotate(
        child_count=Coalesce(Subquery(children_qs), 0),
        image_count=Coalesce(Subquery(image_qs), 0),
    )


@router.get("/", response=list[ImageFolderSchema], operation_id="folder_list_roots")
def list_image_folders(request):
    """List root image folders with permission filtering"""
    user = request.user
    perm_filter = get_permission_filter(user)

    # Get root folders
    roots = ImageFolder.get_roots_queryset().values_list("pk", flat=True)
    queryset = ImageFolder.objects.prefetch_related("view_groups", "edit_groups").filter(pk__in=roots).order_by("name")

    # Apply permission filtering to base queryset if not superuser
    if not user.is_superuser:
        queryset = queryset.filter(perm_filter).distinct()

    # Annotate with counts
    return annotate_folder_counts(queryset, perm_filter)


@router.get("/{folder_id}/", response=ImageFolderDetailSchema, operation_id="folder_get_details")
def get_image_folder(request, folder_id: int):
    """Get details of a specific image folder with children and images"""
    user = request.user
    perm_filter = get_permission_filter(user)

    # Get folder with permission check
    folder = get_object_or_404(ImageFolder.objects.prefetch_related("view_groups", "edit_groups"), pk=folder_id)

    # Check permissions if not superuser
    if not user.is_superuser:
        has_perm = (
            folder.view_groups.filter(pk__in=user.groups.values_list("pk", flat=True)).exists()
            or not folder.view_groups.exists()
            or folder.edit_groups.filter(pk__in=user.groups.values_list("pk", flat=True)).exists()
        )
        if not has_perm:
            raise HttpNotAuthorizedError("Unable to view this folder")

    # Get child folders with permission filtering
    child_folders = ImageFolder.objects.filter(tn_parent=folder).order_by("name")
    if not user.is_superuser:
        child_folders = child_folders.filter(perm_filter).distinct()

    # Annotate child folders with counts
    child_folders = annotate_folder_counts(child_folders, perm_filter)

    # Get images with permission filtering
    images = Image.objects.filter(folder=folder)
    if not user.is_superuser:
        images = images.filter(perm_filter).distinct()

    image_custom_data = []

    for image in images:
        # Start building the dictionary for this image
        image_custom_data.append(
            {
                "id": image.id,
                "title": image.title,
                "thumbnail_width": image.thumbnail_width,
                "thumbnail_height": image.thumbnail_height,
                "thumbnail_url": request.build_absolute_uri(image.thumbnail_url),
            },
        )

    # Prepare breadcrumbs
    ancestors = list(folder.get_ancestors_queryset())
    breadcrumb_objects = [*ancestors, folder]
    breadcrumbs = []
    for obj in breadcrumb_objects:
        breadcrumbs.append(  # noqa: PERF401
            {
                "name": obj.name,
                "id": obj.pk,
            },
        )

    # Format response
    return {
        "id": folder.pk,
        "name": folder.name,
        "child_folders": list(child_folders.values("id", "name", "child_count", "image_count")),
        "folder_images": image_custom_data,
        "breadcrumbs": breadcrumbs,
        "has_children": child_folders.exists(),
        "image_count": images.count(),
    }
