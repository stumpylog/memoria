from ninja import Schema

from memoria.routes.images.schemas import ImageThumbnailSchema


class BreadcrumbSchema(Schema):
    name: str
    id: int


class ImageFolderSchema(Schema):
    id: int
    name: str
    description: str | None
    child_count: int = 0
    image_count: int = 0


class ImageFolderDetailSchema(Schema):
    id: int
    name: str
    child_folders: list[ImageFolderSchema]
    folder_images: list[ImageThumbnailSchema]
    breadcrumbs: list[BreadcrumbSchema]
    has_children: bool
    image_count: int
