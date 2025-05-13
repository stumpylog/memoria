from ninja import Schema


class BreadcrumbSchema(Schema):
    name: str
    id: int


class ImageSchema(Schema):
    id: int
    title: str
    thumbnail_url: str


class ImageFolderSchema(Schema):
    id: int
    name: str
    child_count: int = 0
    image_count: int = 0


class ImageFolderDetailSchema(Schema):
    id: int
    name: str
    child_folders: list[ImageFolderSchema]
    folder_images: list[ImageSchema]
    breadcrumbs: list[BreadcrumbSchema]
    has_children: bool
    image_count: int
