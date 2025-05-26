import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import HttpRequest
from ninja import Router

from memoria.common.auth import active_staff_or_superuser_auth
from memoria.models import Album
from memoria.models import Image
from memoria.models import ImageFolder
from memoria.models import ImageSource
from memoria.models import Person
from memoria.models import Pet
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.models import SiteSettings
from memoria.models import Tag
from memoria.routes.system.schemas import SiteSettingsSchemaOut
from memoria.routes.system.schemas import SiteSettingsUpdateSchemaIn
from memoria.routes.system.schemas import StatisticsResponseSchema
from memoria.routes.system.schemas import SystemStatisticsSchema
from memoria.routes.system.schemas import UserStatisticsSchema

router = Router(tags=["system"])

logger = logging.getLogger(__name__)


def get_disk_usage_gb(path: Path) -> tuple[float, float, float]:
    """
    Calculates disk usage for a given path in gigabytes.
    Returns (total, used, free).
    """
    try:
        total, used, free = shutil.disk_usage(path)
        # Convert bytes to gigabytes
        gb_factor = 1024**3
        return total / gb_factor, used / gb_factor, free / gb_factor
    except Exception:
        # Handle cases where the path might not exist or be accessible
        return 0.0, 0.0, 0.0


@router.get(
    "/settings/",
    response=SiteSettingsSchemaOut,
    operation_id="get_system_settings",
    auth=active_staff_or_superuser_auth,
)
def get_system_settings(
    request: HttpRequest,
):
    return SiteSettings.objects.first()


@router.patch(
    "/settings/",
    response=SiteSettingsSchemaOut,
    operation_id="update_system_settings",
    auth=active_staff_or_superuser_auth,
)
def update_system_settings(
    request: HttpRequest,
    data: SiteSettingsUpdateSchemaIn,
):
    settings_obj = SiteSettings.objects.first()
    if TYPE_CHECKING:
        assert settings_obj is not None
    if data.large_image_max_size is not None:
        settings_obj.large_image_max_size = data.large_image_max_size.value

    if data.large_image_quality is not None:
        settings_obj.large_image_quality = data.large_image_quality

    if data.thumbnail_max_size is not None:
        settings_obj.thumbnail_max_size = data.thumbnail_max_size.value

    settings_obj.save()

    return settings_obj


@router.get("/statistics/", response=StatisticsResponseSchema, operation_id="get_system_statistics")
def get_system_statistics(
    request: HttpRequest,
):
    """
    Returns statistics about the system, including counts of various objects
    and disk space usage, filtered by the current user's view/edit permissions.
    System-wide object counts are no longer exposed to prevent information leakage.
    """
    user = request.user

    # --- User-specific statistics ---
    user_stats = UserStatisticsSchema(
        total_images_viewable=Image.objects.viewable_by(user).count(),
        total_images_editable=Image.objects.editable_by(user).count(),
        total_albums_viewable=Album.objects.viewable_by(user).count(),
        total_albums_editable=Album.objects.editable_by(user).count(),
        total_tags_viewable=Tag.objects.viewable_by(user).count(),
        total_tags_editable=Tag.objects.editable_by(user).count(),
        total_people_viewable=Person.objects.viewable_by(user).count(),
        total_people_editable=Person.objects.editable_by(user).count(),
        total_pets_viewable=Pet.objects.viewable_by(user).count(),
        total_pets_editable=Pet.objects.editable_by(user).count(),
        total_folders_viewable=ImageFolder.objects.viewable_by(user).count(),
        total_folders_editable=ImageFolder.objects.editable_by(user).count(),
        total_sources_viewable=ImageSource.objects.viewable_by(user).count(),
        total_sources_editable=ImageSource.objects.editable_by(user).count(),
        total_rough_dates_viewable=RoughDate.objects.viewable_by(user).count(),
        total_rough_dates_editable=RoughDate.objects.editable_by(user).count(),
        total_rough_locations_viewable=RoughLocation.objects.viewable_by(user).count(),
        total_rough_locations_editable=RoughLocation.objects.editable_by(user).count(),
    )

    # --- System-wide statistics (only non-sensitive info like disk space) ---
    system_stats = SystemStatisticsSchema(
        disk_total_space_gb=None,
        disk_used_space_gb=None,
        disk_free_space_gb=None,
    )

    # Add disk space information if MEDIA_ROOT is defined and accessible
    if hasattr(settings, "MEDIA_ROOT") and isinstance(settings.MEDIA_ROOT, str | Path):
        media_root_path = Path(settings.MEDIA_ROOT)
        if media_root_path.exists():
            total_gb, used_gb, free_gb = get_disk_usage_gb(media_root_path)
            system_stats.disk_total_space_gb = round(total_gb, 2)
            system_stats.disk_used_space_gb = round(used_gb, 2)
            system_stats.disk_free_space_gb = round(free_gb, 2)

    return StatisticsResponseSchema(
        user_statistics=user_stats,
        system_statistics=system_stats,
    )
