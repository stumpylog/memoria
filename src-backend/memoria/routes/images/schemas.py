import datetime
from datetime import date
from typing import TYPE_CHECKING

from django.db.models import Q
from django.http import HttpRequest
from exifmwg.models import RotationEnum
from ninja import Field
from ninja import FilterSchema
from ninja import Schema
from pydantic import FilePath
from pydantic import field_serializer
from pydantic import model_validator

from memoria.models import Image
from memoria.routes.common.schemas import GroupPermissionReadOutMixin
from memoria.routes.common.schemas import GroupPermissionUpdateInMixin
from memoria.routes.common.schemas import IdMixin

if TYPE_CHECKING:
    from django.http import HttpRequest


class ImageBooleanFilterSchema(FilterSchema):
    is_dirty: bool | None = Field(None, description="Filter by dirty status")
    is_starred: bool | None = Field(None, description="Filter by starred status")
    is_deleted: bool | None = Field(None, description="Filter by deletion status")

    def filter_queryset(self, queryset):
        if self.is_dirty is not None:
            queryset = queryset.filter(is_dirty=self.is_dirty)

        if self.is_starred is not None:
            queryset = queryset.filter(is_starred=self.is_starred)

        if self.is_deleted is not None:
            if self.is_deleted:
                queryset = queryset.exclude(deleted_at__isnull=True)
            else:
                queryset = queryset.filter(deleted_at__isnull=True)

        return queryset


class ImageFKFilterSchema(FilterSchema):
    folder_id: int | None = Field(None, description="Filter by ImageFolder ID")

    def filter_queryset(self, queryset):
        if self.folder_id is not None:
            queryset = queryset.filter(folder_id=self.folder_id)

        return queryset


class ImageM2MFilterSchema(FilterSchema):
    people_ids: list[int] | None = Field(None, description="Filter by Person IDs")
    pets_ids: list[int] | None = Field(None, description="Filter by Pet IDs")
    tags_ids: list[int] | None = Field(None, description="Filter by Tag IDs")

    def filter_queryset(self, queryset):
        if self.people_ids:
            queryset = queryset.filter(people__id__in=self.people_ids).distinct()

        if self.pets_ids:
            queryset = queryset.filter(pets__id__in=self.pets_ids).distinct()

        if self.tags_ids:
            queryset = queryset.filter(tags__id__in=self.tags_ids).distinct()

        return queryset


# RoughLocation filter schema
class RoughLocationFilterSchema(FilterSchema):
    country_code: str | None = Field(None, description="Filter by country code (ISO 3166-1 alpha 2)")
    subdivision_code: str | None = Field(None, description="Filter by state/province code (ISO 3166-2)")
    city: str | None = Field(None, description="Filter by city name (partial match)")
    sub_location: str | None = Field(None, description="Filter by sub-location (partial match)")

    def filter_queryset(self, queryset):
        if self.country_code is not None:
            queryset = queryset.filter(location__country_code=self.country_code)

        if self.subdivision_code is not None:
            queryset = queryset.filter(location__subdivision_code=self.subdivision_code)

        if self.city is not None:
            queryset = queryset.filter(location__city__icontains=self.city)

        if self.sub_location is not None:
            queryset = queryset.filter(location__sub_location__icontains=self.sub_location)

        return queryset


class RoughDateComparisonFilterSchema(FilterSchema):
    date_start: date | None = Field(None, description="Filter images from this date onwards using comparison_date")
    date_end: date | None = Field(None, description="Filter images up to this date using comparison_date")
    year_start: int | None = Field(None, description="Filter images from this year onwards")
    year_end: int | None = Field(None, description="Filter images up to this year")
    month_start: int | None = Field(
        None,
        description="Filter images from this month onwards (1-12, includes null months)",
    )
    month_end: int | None = Field(None, description="Filter images up to this month (1-12, includes null months)")
    day_start: int | None = Field(None, description="Filter images from this day onwards (1-31, includes null days)")
    day_end: int | None = Field(None, description="Filter images up to this day (1-31, includes null days)")

    @model_validator(mode="after")
    def validate_date_hierarchy(self):
        # Day filters require month filters
        # Month filters require year filters
        if self.day_start is not None and self.month_start is None:
            raise ValueError("Starting day filter is missing a starting month")  # noqa: EM101, TRY003
        if self.month_start is not None and self.year_start is None:
            raise ValueError("Starting month filter is missing a starting year value")  # noqa: EM101, TRY003

        if self.date_end is not None and self.month_end is None:
            raise ValueError("Ending day filter is missing an ending month")  # noqa: EM101, TRY003
        if self.month_end is not None and self.year_end is None:
            raise ValueError("Ending month filter is missing an ending year value")  # noqa: EM101, TRY003
        return self

    def filter_queryset(self, queryset):
        filters = Q()

        # Use comparison_date for precise date range filtering
        if self.date_start is not None:
            filters &= Q(comparison_date__gte=self.date_start)
        if self.date_end is not None:
            filters &= Q(comparison_date__lte=self.date_end)

        # Individual field filtering for more granular control
        if self.year_start is not None:
            filters &= Q(year__gte=self.year_start)
        if self.year_end is not None:
            filters &= Q(year__lte=self.year_end)

        # For month/day, include nulls to match "incomplete" dates
        if self.year_start:
            filters &= Q(year__gte=self.year_start)
        if self.year_end:
            filters &= Q(year__lte=self.year_end)
        if self.month_start:
            filters &= Q(month__gte=self.month_start)
        if self.month_end:
            filters &= Q(month__lte=self.month_end)
        if self.day_start:
            filters &= Q(day__gte=self.day_start)
        if self.day_end:
            filters &= Q(day__lte=self.day_end)

        return queryset.filter(filters)


class ImageThumbnailSchemaOut(IdMixin, Schema):
    title: str
    thumbnail_url: str
    thumbnail_height: int
    thumbnail_width: int

    @staticmethod
    def resolve_thumbnail_url(obj: Image, context):
        """
        Build absolute URL for the thumbnail image
        """
        request: HttpRequest | None = context.get("request")
        if request:
            return request.build_absolute_uri(obj.thumbnail_url)
        return obj.thumbnail_url


class ImageDateSchemaOut(Schema):
    date: date
    month_valid: bool
    day_valid: bool


class ImageDateUpdateSchemaIn(Schema):
    date: date
    month_valid: bool
    day_valid: bool


class ImageLocationSchemaOut(Schema):
    country_code: str
    country_name: str
    subdivision_code: str | None
    subdivision_name: str | None
    city: str | None
    sub_location: str | None


class ImageLocationUpdateSchemaIn(Schema):
    country_code: str
    subdivision_code: str | None
    city: str | None
    sub_location: str | None


class ImageSizeSchemaOut(Schema):
    original_height: int
    original_width: int
    large_version_height: int
    large_version_width: int


class ImageFolderSchemaOut(Schema):
    id: int
    name: str


class ImageMetadataSchemaOut(IdMixin, GroupPermissionReadOutMixin, Schema):
    larger_size_url: str
    orientation: RotationEnum
    size: ImageSizeSchemaOut
    title: str
    description: str | None
    file_size: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    original_checksum: str
    phash: str
    original_path: FilePath
    image_fs_id: str
    can_edit: bool
    folder: ImageFolderSchemaOut

    @field_serializer("original_path")
    def convert_path_to_str(self, v) -> str:
        return str(v)

    @staticmethod
    def resolve_larger_size_url(obj, context):
        """
        Build absolute URL for the larger size image
        """
        request: HttpRequest | None = context.get("request")
        if request:
            return request.build_absolute_uri(obj.larger_size_url)
        return obj.larger_size_url

    @staticmethod
    def resolve_size(obj):
        """
        Create size object from individual model fields
        """
        return ImageSizeSchemaOut(
            original_height=obj.original_height,
            original_width=obj.original_width,
            large_version_height=obj.large_version_height,
            large_version_width=obj.large_version_width,
        )

    @staticmethod
    def resolve_folder(obj):
        """
        Create folder object from annotated fields
        """
        return ImageFolderSchemaOut(
            id=obj.folder.id,
            name=obj.folder.name,
        )


class ImageMetadataUpdateSchemaIn(GroupPermissionUpdateInMixin, Schema):
    title: str | None
    description: str | None


class BoxInImageBaseSchema(Schema):
    """
    Base schema for models inheriting from AbstractBoxInImage.
    Represents a bounding box within an image and includes timestamps.
    """

    id: int
    center_x: float
    center_y: float
    height: float
    width: float


class PersonInImageSchemaOut(BoxInImageBaseSchema):
    """
    Schema for representing a PersonInImage instance.
    Details a specific person's bounding box in an image.
    """

    person_id: int
    name: str


class PetInImageSchemaOut(BoxInImageBaseSchema):
    """
    Schema for representing a PetInImage instance.
    Details a specific pet's bounding box in an image.
    """

    pet_id: int | None = None
    name: str
