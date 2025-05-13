import logging

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from memoria.common.auth import active_user_auth
from memoria.common.errors import HttpNotAuthorizedError
from memoria.models import Image
from memoria.routes.images.schemas import ImageDetailSchema
from memoria.routes.images.schemas import ImageThumbnailSchema

router = Router(tags=["images"])
logger = logging.getLogger(__name__)
UserModelT = get_user_model()


def get_permission_filter(user: UserModelT):
    """
    Generate permission filter based on user groups
    TODO: De-duplicate this
    """
    if user.is_superuser:
        return Q()
    groups = user.groups.all()
    return Q(view_groups__in=groups) | Q(edit_groups__in=groups)


@router.get(
    "/{image_id}/thumbnail/",
    response=ImageThumbnailSchema,
    auth=active_user_auth,
    operation_id="image_get_thumb_info",
)
def get_image_thumbnail_info(request: HttpRequest, image_id: int):
    img = get_object_or_404(Image.objects.prefetch_related("view_groups", "edit_groups"), pk=image_id)
    if not request.user.is_superuser:
        has_perm = (
            img.view_groups.filter(id__in=request.user.groups.all()).exists()
            or img.edit_groups.filter(id__in=request.user.groups.all()).exists()
        )
        if not has_perm:
            raise HttpNotAuthorizedError("Unable to view this folder")
    return img


@router.get(
    "/{image_id}/metadata/",
    response=ImageDetailSchema,
    auth=active_user_auth,
    operation_id="image_detail_info",
)
def get_image_details(request: HttpRequest, image_id: int):
    pass
