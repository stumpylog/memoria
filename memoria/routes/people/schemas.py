import sys

from ninja import Schema
from pydantic import model_validator

if sys.version_info > (3, 11):
    from typing import Self
else:
    from typing import Self


class PersonCreateInSchema(Schema):
    """
    Schema to create a Person
    """

    name: str
    description: str | None = None


class PersonReadOutSchema(PersonCreateInSchema):
    """
    Schema when reading a person
    """

    id: int


class PersonUpdateInSchema(Schema):
    """
    Schema to update a person
    """

    name: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def check_one_or_other(self) -> Self:
        if self.name is None and self.description is None:
            raise ValueError("At least one of name or description must be set")  # noqa: TRY003, EM101
        return self
