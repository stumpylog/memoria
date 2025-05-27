import sys

from ninja import Schema
from pydantic import Field

if sys.version_info > (3, 11):
    pass
else:
    pass


class PersonCreateInSchema(Schema):
    """
    Schema to create a Person
    """

    name: str
    description: str | None = None


class PersonReadOutSchema(Schema):
    """
    Schema when reading a person
    """

    id: int
    name: str
    image_count: int
    description: str | None = None


class PersonDetailOutSchema(Schema):
    id: int
    name: str
    image_count: int
    description: str | None = None


class PersonImageOutSchema(Schema):
    id: int = Field(description="One image the person appears in")


class PersonUpdateInSchema(Schema):
    """
    Schema to update a person
    """

    name: str | None = None
    description: str | None = None
