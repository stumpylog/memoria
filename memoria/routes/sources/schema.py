import sys

from ninja import Schema
from pydantic import model_validator

if sys.version_info > (3, 11):
    from typing import Self
else:
    from typing import Self


class ImageSourceCreateInSchema(Schema):
    name: str
    description: str | None = None


class ImageSourceReadOutSchema(ImageSourceCreateInSchema):
    id: int


class ImageSourceUpdateInSchema(Schema):
    name: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> Self:
        if not (self.name or self.description):
            raise ValueError("At least one field must be updated.")  # noqa: TRY003, EM101
        return self
