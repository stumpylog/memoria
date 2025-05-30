import logging

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from memoria.common.errors import HttpNotAuthorizedError
from memoria.models import Image
from memoria.models import ImageFolder
from memoria.routes.folders.schemas import FolderDetailSchemaOut
from memoria.routes.folders.schemas import FolderUpdateSchemaIn
from memoria.routes.folders.schemas import RootFolderSchemaOut

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
    """
    Annotate folders with child and image counts
    """
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


@router.get("/", response=list[RootFolderSchemaOut], operation_id="folder_list_roots")
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


@router.get("/{folder_id}/", response=FolderDetailSchemaOut, operation_id="folder_get_details")
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
            msg = "Unable to view this folder"
            logger.warning(msg)
            raise HttpNotAuthorizedError(msg)

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
        "description": folder.description,
        "child_folders": list(child_folders.values("id", "name", "child_count", "image_count", "description")),
        "folder_images": images.values_list("id", flat=True),
        "breadcrumbs": breadcrumbs,
        "has_children": child_folders.exists(),
        "updated_at": folder.updated_at,
        "created_at": folder.created_at,
        "view_groups": folder.view_groups.all(),
        "edit_groups": folder.edit_groups.all(),
    }


@router.patch("/{folder_id}/", response=FolderDetailSchemaOut, operation_id="update_folder_info")
def update_folder(request: HttpRequest, folder_id: int, data: FolderUpdateSchemaIn):
    folder_to_update: ImageFolder = get_object_or_404(ImageFolder.objects.editable_by(request.user), pk=folder_id)

    # TODO: Maybe the name?

    if data.description:
        folder_to_update.description = data.description

    if data.view_group_ids:
        folder_to_update.view_groups.set(data.view_group_ids)
    if data.edit_group_ids:
        folder_to_update.edit_groups.set(data.edit_group_ids)

    folder_to_update.save()
    folder_to_update.refresh_from_db()

    ancestors = list(folder_to_update.get_ancestors_queryset())
    breadcrumb_objects = [*ancestors, folder_to_update]
    breadcrumbs = []
    for obj in breadcrumb_objects:
        breadcrumbs.append(  # noqa: PERF401
            {
                "name": obj.name,
                "id": obj.pk,
            },
        )

    perm_filter = get_permission_filter(request.user)

    # Get child folders with permission filtering
    child_folders = ImageFolder.objects.filter(tn_parent=folder_to_update).order_by("name")
    if not request.user.is_superuser:
        child_folders = child_folders.filter(perm_filter).distinct()

    images = Image.objects.filter(folder=folder_to_update)
    if not request.user.is_superuser:
        images = images.filter(perm_filter).distinct()

    # Annotate child folders with counts
    child_folders = annotate_folder_counts(child_folders, perm_filter)

    return {
        "id": folder_to_update.pk,
        "name": folder_to_update.name,
        "description": folder_to_update.description,
        "child_folders": list(child_folders.values("id", "name", "child_count", "image_count", "description")),
        "folder_images": images.values_list("id", flat=True),
        "breadcrumbs": breadcrumbs,
        "has_children": child_folders.exists(),
        "view_groups": folder_to_update.view_groups.all(),
        "edit_groups": folder_to_update.edit_groups.all(),
        "updated_at": folder_to_update.updated_at,
        "created_at": folder_to_update.created_at,
    }
