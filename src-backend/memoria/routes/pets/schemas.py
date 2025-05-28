import sys

from ninja import Field
from ninja import Schema
from pydantic import model_validator

if sys.version_info > (3, 11):
    from enum import StrEnum
    from typing import Self
else:
    from enum import Enum
    from typing import Self

    class StrEnum(str, Enum):
        pass


from memoria.routes.common.schemas import GroupPermissionReadOutMixin
from memoria.routes.common.schemas import GroupPermissionUpdateInMixin
from memoria.routes.common.schemas import TimestampMixin


class PetTypeChoices(StrEnum):
    CAT = "cat"
    DOG = "dog"
    HORSE = "horse"


class PetReadSchemaOut(Schema):
    """
    Schema when reading a pet
    """

    id: int
    name: str
    image_count: int
    description: str | None = None
    pet_type: PetTypeChoices | None = None


class PetReadDetailSchemaOut(TimestampMixin, GroupPermissionReadOutMixin, Schema):
    """
    Schema when reading a pet
    """

    id: int
    name: str
    description: str | None = None
    pet_type: PetTypeChoices | None = None


class PetImageOutSchema(Schema):
    id: int = Field(description="One image the pet appears in")


class PetUpdateInSchema(GroupPermissionUpdateInMixin, Schema):
    """
    Schema to update a pet
    """

    name: str | None = None
    description: str | None = None
    pet_type: PetTypeChoices | None = None

    @model_validator(mode="after")
    def check_one_or_other(self) -> Self:
        if self.name is None and self.description is None and self.pet_type is None:
            raise ValueError("At least one of name, description or type must be set")  # noqa: TRY003, EM101
        return self
