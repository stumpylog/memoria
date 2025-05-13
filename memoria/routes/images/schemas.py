from ninja import Field
from ninja import Schema
from scansteward.imageops.models import RotationEnum


class Album(Schema):
    id: int
    name: str
    description: str | None = None


class BoundingBoxSchema(Schema):
    center_x: float = Field(description="Center X coordinate of the bounding box", ge=0.0, le=1.0)
    center_y: float = Field(description="Center Y coordinate of the bounding box", ge=0.0, le=1.0)
    height: float = Field(description="Height of the bounding box", gt=0.0, lt=1.0)
    width: float = Field(description="Width of the bounding box", gt=0.0, lt=1.0)


class PersonWithBoxSchema(Schema):
    person_id: int = Field(description="Person ID")
    box: BoundingBoxSchema = Field(description="Bounding box of the person's face")


class PersonFaceDeleteSchema(Schema):
    people_ids: list[int] = Field(description="List of people to delete from the image")


class PetWithBoxSchema(Schema):
    pet_id: int = Field(description="Pet ID")
    box: BoundingBoxSchema = Field(description="Bounding box of the pet")


class PetBoxDeleteInSchema(Schema):
    pet_ids: list[int] = Field(description="List of pets to delete from the image")


class ImageMetadataOutSchema(Schema):
    orientation: RotationEnum
    description: str | None = None
    location_id: int | None = None
    date_id: int | None = None


class ImageMetadataUpdateInSchema(Schema):
    description: str | None = None

    orientation: RotationEnum | None = None

    location_id: int | None = None
    date_id: int | None = None
