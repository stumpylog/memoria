from ninja import Field
from ninja import Schema


class BreadcrumbSchema(Schema):
    name: str
    id: int


class RootFolderSchema(Schema):
    id: int
    name: str
    description: str | None
    child_count: int = 0
    image_count: int = 0
    view_group_ids: list[int] = Field(default_factory=list, description="IDs of Groups allowed to view")
    edit_group_ids: list[int] = Field(default_factory=list, description="IDs of Groups allowed to edit")


class FolderDetailSchema(Schema):
    id: int
    name: str
    child_folders: list[RootFolderSchema]
    folder_images: list[int]
    breadcrumbs: list[BreadcrumbSchema]
    has_children: bool
    view_group_ids: list[int] = Field(default_factory=list, description="IDs of Groups allowed to view")
    edit_group_ids: list[int] = Field(default_factory=list, description="IDs of Groups allowed to edit")
