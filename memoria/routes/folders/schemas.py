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


class FolderDetailSchema(Schema):
    id: int
    name: str
    child_folders: list[RootFolderSchema]
    folder_images: list[int]
    breadcrumbs: list[BreadcrumbSchema]
    has_children: bool
