import datetime
from datetime import date

# TODO: use HttpUrl for the URLs, except orjson doesn't serialize them
from exifmwg.models import RotationEnum
from ninja import Schema
from pydantic import FilePath
from pydantic import field_serializer


class ImageThumbnailSchema(Schema):
    id: int
    title: str
    thumbnail_url: str
    thumbnail_height: int
    thumbnail_width: int


class ImageDateSchema(Schema):
    date: date
    month_valid: bool
    day_valid: bool


class ImageLocationSchema(Schema):
    country_code: str
    country_name: str
    subdivision_code: str | None
    subdivision_name: str | None
    city: str | None
    sub_location: str | None


class ImageMetadataSchema(Schema):
    id: int
    larger_size_url: str
    orientation: RotationEnum
    original_height: int
    original_width: int
    title: str
    file_size: int
    description: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    original_checksum: str
    phash: str
    original_path: FilePath
    image_fs_id: str

    @field_serializer("original_path")
    def convert_path_to_str(self, v) -> str:
        return str(v)


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
