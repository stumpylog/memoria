from datetime import date

from exifmwg.models import RotationEnum
from ninja import Schema
from pydantic import HttpUrl


class ImageThumbnailSchema(Schema):
    id: int
    title: str
    thumbnail_url: HttpUrl
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


class ImageDetailSchema(Schema):
    id: int
    full_size_url: HttpUrl
    orientation: RotationEnum
    original_height: int
    original_width: int
    title: str
    file_size: int
    description: str | None
