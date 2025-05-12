import sys

from ninja import Schema
from pydantic import model_validator

if sys.version_info > (3, 11):
    from typing import Self
else:
    from typing import Self


class PetCreateInSchema(Schema):
    """
    Schema to create a Pet
    """

    name: str
    description: str | None = None


class PetReadOutSchema(PetCreateInSchema):
    """
    Schema when reading a pet
    """

    id: int


class PetUpdateInSchema(Schema):
    """
    Schema to update a pet
    """

    name: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def check_one_or_other(self) -> Self:
        if self.name is None and self.description is None:
            raise ValueError("At least one of name or description must be set")  # noqa: TRY003, EM101
        return self
