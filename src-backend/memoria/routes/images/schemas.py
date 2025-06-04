import datetime
from datetime import date
from typing import TYPE_CHECKING

from django.http import HttpRequest
from exifmwg.models import RotationEnum
from ninja import Schema
from pydantic import Field
from pydantic import FilePath
from pydantic import field_serializer

from memoria.models import Image
from memoria.routes.common.schemas import GroupPermissionReadOutMixin
from memoria.routes.common.schemas import GroupPermissionUpdateInMixin
from memoria.routes.common.schemas import IdMixin

if TYPE_CHECKING:
    from django.http import HttpRequest


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
    comparison_date: date
    year: int
    month: int | None = None
    day: int | None = None

    month_valid: bool = Field(True)  # Set a default, will be overridden
    day_valid: bool = Field(True)  # Set a default, will be overridden

    def model_post_init(self, __context) -> None:
        # At this point, self.month and self.day will have their final values
        # derived from comparison_date or explicitly provided.
        self.month_valid = self.month is not None
        self.day_valid = self.day is not None


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
