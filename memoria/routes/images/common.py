from typing import TYPE_CHECKING

from scansteward.imageops.models import RotationEnum
from scansteward.models import Image
from scansteward.models import PersonInImage
from scansteward.models import PetInImage
from scansteward.routes.images.schemas import BoundingBoxSchema
from scansteward.routes.images.schemas import ImageMetadataOutSchema
from scansteward.routes.images.schemas import PersonWithBoxSchema
from scansteward.routes.images.schemas import PetWithBoxSchema


async def get_faces_from_image(image: Image) -> list[PersonWithBoxSchema]:
    all_people_in_image = image.people.prefetch_related("images").all()

    boxes: list[PersonWithBoxSchema] = []
    async for person in all_people_in_image:
        bounding_box: PersonInImage = await person.images.aget(image=image, person=person)

        if TYPE_CHECKING:
            assert bounding_box is not None
            assert isinstance(bounding_box, PersonInImage)

        boxes.append(
            PersonWithBoxSchema(
                person_id=person.pk,
                box=BoundingBoxSchema(
                    center_x=bounding_box.center_x,
                    center_y=bounding_box.center_y,
                    height=bounding_box.height,
                    width=bounding_box.width,
                ),
            ),
        )

    return boxes


async def get_pet_boxes_from_image(image: Image) -> list[PetWithBoxSchema]:
    all_pets_in_image = image.pets.prefetch_related("images").all()

    boxes: list[PetWithBoxSchema] = []
    async for pet in all_pets_in_image:
        bounding_box: PetInImage = await pet.images.aget(image=image, pet=pet)

        if TYPE_CHECKING:
            assert bounding_box is not None
            assert isinstance(bounding_box, PetInImage)

        boxes.append(
            PetWithBoxSchema(
                pet_id=pet.pk,
                box=BoundingBoxSchema(
                    center_x=bounding_box.center_x,
                    center_y=bounding_box.center_y,
                    height=bounding_box.height,
                    width=bounding_box.width,
                ),
            ),
        )

    return boxes


async def get_image_metadata_common(image: Image) -> ImageMetadataOutSchema:
    return ImageMetadataOutSchema(
        orientation=RotationEnum(image.orientation),
        description=image.description,
        location_id=image.location.pk if image.location else None,
        date_id=image.date.pk if image.date else None,
    )
