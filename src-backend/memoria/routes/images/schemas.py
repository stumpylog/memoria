import datetime
from datetime import date
from typing import TYPE_CHECKING

from django.db.models import Q
from django.http import HttpRequest
from exifmwg.models import RotationEnum
from ninja import FilterSchema
from ninja import Schema
from pydantic import FilePath
from pydantic import field_serializer

from memoria.models import Image
from memoria.routes.common.schemas import GroupPermissionReadOutMixin
from memoria.routes.common.schemas import GroupPermissionUpdateInMixin
from memoria.routes.common.schemas import IdMixin

if TYPE_CHECKING:
    from django.http import HttpRequest


class ImageBooleanFilterSchema(FilterSchema):
    is_dirty: bool | None = None
    is_starred: bool | None = None
    is_deleted: bool | None = None

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
    source_id: int | None = None
    location_id: int | None = None
    date_id: int | None = None
    folder_id: int | None = None

    def filter_queryset(self, queryset):
        if self.source_id is not None:
            queryset = queryset.filter(source_id=self.source_id)

        if self.location_id is not None:
            queryset = queryset.filter(location_id=self.location_id)

        if self.date_id is not None:
            queryset = queryset.filter(date_id=self.date_id)

        if self.folder_id is not None:
            queryset = queryset.filter(folder_id=self.folder_id)

        return queryset


class ImageM2MFilterSchema(FilterSchema):
    people_ids: list[int] | None = None
    pets_ids: list[int] | None = None
    tags_ids: list[int] | None = None

    def filter_queryset(self, queryset):
        if self.people_ids:
            queryset = queryset.filter(people__id__in=self.people_ids).distinct()

        if self.pets_ids:
            queryset = queryset.filter(pets__id__in=self.pets_ids).distinct()

        if self.tags_ids:
            queryset = queryset.filter(tags__id__in=self.tags_ids).distinct()

        return queryset


class RoughDateComparisonFilterSchema(FilterSchema):
    date_start: date | None = None
    date_end: date | None = None
    year_start: int | None = None
    year_end: int | None = None
    month_start: int | None = None
    month_end: int | None = None
    day_start: int | None = None
    day_end: int | None = None

    def filter_queryset(self, queryset):
        filters = Q()

        # Use comparison_date for precise date range filtering
        if self.date_start is not None:
            filters &= Q(date__comparison_date__gte=self.date_start)
        if self.date_end is not None:
            filters &= Q(date__comparison_date__lte=self.date_end)

        # Individual field filtering for more granular control
        if self.year_start is not None:
            filters &= Q(date__year__gte=self.year_start)
        if self.year_end is not None:
            filters &= Q(date__year__lte=self.year_end)

        # For month/day, include nulls to match "incomplete" dates
        if self.month_start is not None:
            filters &= Q(
                Q(date__month__gte=self.month_start) | Q(date__month__isnull=True),
            )
        if self.month_end is not None:
            filters &= Q(
                Q(date__month__lte=self.month_end) | Q(date__month__isnull=True),
            )

        if self.day_start is not None:
            filters &= Q(
                Q(date__day__gte=self.day_start) | Q(date__day__isnull=True),
            )
        if self.day_end is not None:
            filters &= Q(
                Q(date__day__lte=self.day_end) | Q(date__day__isnull=True),
            )

        return queryset.filter(filters)


class RoughLocationFilterSchema(FilterSchema):
    country_code: str | None = None
    subdivision_code: str | None = None
    city: str | None = None
    sub_location: str | None = None

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
