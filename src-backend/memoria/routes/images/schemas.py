import datetime
from datetime import date

# TODO: use HttpUrl for the URLs, except orjson doesn't serialize them
from exifmwg.models import RotationEnum
from ninja import Field
from ninja import Schema
from pydantic import FilePath
from pydantic import field_serializer


class ImageThumbnailSchemaOut(Schema):
    id: int
    title: str
    thumbnail_url: str
    thumbnail_height: int
    thumbnail_width: int


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


class ImageMetadataSchemaOut(Schema):
    id: int
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
    view_group_ids: list[int] = Field(default_factory=list, description="IDs of Groups allowed to view")
    edit_group_ids: list[int] = Field(default_factory=list, description="IDs of Groups allowed to edit")

    @field_serializer("original_path")
    def convert_path_to_str(self, v) -> str:
        return str(v)


class ImageMetadataUpdateSchemaIn(Schema):
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
