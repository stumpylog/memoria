import enum

from ninja import Schema
from pydantic import Field


@enum.unique
class ImageScaledSideMaxEnum(enum.IntEnum):
    """
    IntEnum for the maximum side length of a scaled image,
    commonly used for responsive image breakpoints.

    Sync with ImageScaledSideMaxChoices
    """

    SMALL = 768
    MEDIUM = 1024
    LARGE = 1920
    XLARGE = 2560
    XXLARGE = 3840


class ThumbnailSizeEnum(enum.IntEnum):
    """
    Defines standard pixel dimensions for image thumbnails using an IntEnum.
    The value represents the maximum dimension (width or height)
    of the thumbnail, with aspect ratio preserved.

    Sync with ThumbnailSizeChoices
    """

    TINY = 128
    SMALL = 256
    MEDIUM = 512
    LARGE = 640
    XLARGE = 800


class SiteSettingsSchemaOut(Schema):
    """
    Schema for outputting site-wide image and quality settings.
    Used for retrieving the current configuration.
    """

    large_image_max_size: ImageScaledSideMaxEnum = Field(
        description="The largest side dimension of generated large images",
    )
    large_image_quality: int = Field(ge=1, le=100, description="The WebP quality setting for generate large images")
    thumbnail_max_size: ThumbnailSizeEnum = Field(
        description="The largest side dimension of generated image thumbnails",
    )


class SiteSettingsUpdateSchemaIn(Schema):
    """
    Schema for updating site settings. All fields are optional to allow
    partial updates (PATCH requests), using Python 3.10+ `| None` syntax.
    """

    large_image_max_size: ImageScaledSideMaxEnum | None = Field(
        None,
        description="The largest side dimension of generated large images",
    )
    large_image_quality: int | None = Field(
        None,
        ge=1,
        le=100,
        description="The WebP quality setting for generate large images",
    )
    thumbnail_max_size: ThumbnailSizeEnum | None = Field(
        None,
        description="The largest side dimension of generated image thumbnails",
    )


class UserStatisticsSchema(Schema):
    """
    Schema for user-specific statistics.
    """

    total_images_viewable: int = Field(..., description="Total number of images the current user can view.")
    total_images_editable: int = Field(..., description="Total number of images the current user can edit.")
    total_albums_viewable: int = Field(..., description="Total number of albums the current user can view.")
    total_albums_editable: int = Field(..., description="Total number of albums the current user can edit.")
    total_tags_viewable: int = Field(..., description="Total number of tags the current user can view.")
    total_tags_editable: int = Field(..., description="Total number of tags the current user can edit.")
    total_people_viewable: int = Field(..., description="Total number of people the current user can view.")
    total_people_editable: int = Field(..., description="Total number of people the current user can edit.")
    total_pets_viewable: int = Field(..., description="Total number of pets the current user can view.")
    total_pets_editable: int = Field(..., description="Total number of pets the current user can edit.")
    total_folders_viewable: int = Field(..., description="Total number of image folders the current user can view.")
    total_folders_editable: int = Field(..., description="Total number of image folders the current user can edit.")
    total_sources_viewable: int = Field(..., description="Total number of image sources the current user can view.")
    total_sources_editable: int = Field(..., description="Total number of image sources the current user can edit.")
    total_rough_dates_viewable: int = Field(..., description="Total number of rough dates the current user can view.")
    total_rough_dates_editable: int = Field(..., description="Total number of rough dates the current user can edit.")
    total_rough_locations_viewable: int = Field(
        ...,
        description="Total number of rough locations the current user can view.",
    )
    total_rough_locations_editable: int = Field(
        ...,
        description="Total number of rough locations the current user can edit.",
    )


class SystemStatisticsSchema(Schema):
    """
    Schema for overall system statistics.
    This now only includes non-sensitive system-level information like disk space.
    """

    disk_total_space_gb: float | None = Field(
        None,
        description="Total disk space available in GB where media files are stored.",
    )
    disk_used_space_gb: float | None = Field(
        None,
        description="Disk space currently used in GB where media files are stored.",
    )
    disk_free_space_gb: float | None = Field(
        None,
        description="Disk space currently free in GB where media files are stored.",
    )


class StatisticsResponseSchema(Schema):
    """
    Combined schema for system and user-specific statistics.
    """

    user_statistics: UserStatisticsSchema = Field(
        ...,
        description="Statistics related to the current user's view and edit permissions.",
    )
    system_statistics: SystemStatisticsSchema = Field(
        ...,
        description="Overall system-level statistics, such as disk usage.",
    )
