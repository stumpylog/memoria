import sys

from ninja import Field
from ninja import Schema
from pydantic import model_validator

if sys.version_info > (3, 11):
    from typing import Self
else:
    from typing import Self


class AlbumCreateInSchema(Schema):
    name: str = Field(description="The name of the album")
    description: str | None = Field(default=None, description="The description of the album")


class AlbumBasicReadOutSchema(AlbumCreateInSchema):
    id: int = Field(description="The id of the album")


class AlbumWithImagesReadInSchema(AlbumBasicReadOutSchema):
    image_ids: list[int] = Field(description="The ids of the images in this album in sorted order")


class AlbumUpdateInSchema(Schema):
    name: str | None = Field(default=None, description="The new name of the album")
    description: str | None = Field(default=None, description="The new description of the album")

    @model_validator(mode="after")
    def check_one_or_other(self) -> Self:
        if self.name is None and self.description is None:
            raise ValueError("At least one of name or description must be set")  # noqa: TRY003, EM101
        return self


class AlbumSortUpdateInSchema(Schema):
    sorting: list[int] = Field(
        description="The new order of the images, with the index being the new position in the album",
    )

    @model_validator(mode="after")
    def check_list_with_items(self) -> Self:
        if self.sorting is not None and not len(self.sorting):
            raise ValueError("No sorting order was defined")  # noqa: TRY003, EM101
        return self


class AlbumAddImageInSchema(Schema):
    image_ids: list[int] = Field(
        default=None,
        description="The id of the image to add to the album",
    )

    @model_validator(mode="after")
    def check_list_with_items(self) -> Self:
        if self.image_ids is not None and not len(self.image_ids):
            raise ValueError("No image IDs were provided")  # noqa: TRY003, EM101
        return self


class AlbumRemoveImageInSchema(Schema):
    image_ids: list[int] = Field(
        default=None,
        description="The id of the image to remove from the album",
    )

    @model_validator(mode="after")
    def check_list_with_items(self) -> Self:
        if self.image_ids is not None and not len(self.image_ids):
            raise ValueError("No image IDs were provided")  # noqa: TRY003, EM101
        return self
