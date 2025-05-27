from ninja import Schema
from pydantic import Field

from memoria.routes.common.schemas import GroupPermissionReadOutMixin
from memoria.routes.common.schemas import GroupPermissionUpdateInMixin
from memoria.routes.common.schemas import TimestampMixin


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


class PersonDetailOutSchema(GroupPermissionReadOutMixin, TimestampMixin, Schema):
    id: int
    name: str
    image_count: int
    description: str | None = None


class PersonImageOutSchema(Schema):
    id: int = Field(description="One image the person appears in")


class PersonUpdateInSchema(GroupPermissionUpdateInMixin, Schema):
    """
    Schema to update a person
    """

    name: str | None = None
    description: str | None = None
