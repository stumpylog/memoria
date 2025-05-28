from ninja import Schema

from memoria.routes.common.schemas import GroupPermissionReadOutMixin
from memoria.routes.common.schemas import GroupPermissionUpdateInMixin
from memoria.routes.common.schemas import TimestampMixin


class BreadcrumbSchema(Schema):
    name: str
    id: int


class RootFolderSchemaOut(GroupPermissionReadOutMixin, Schema):
    id: int
    name: str
    description: str | None
    child_count: int = 0
    image_count: int = 0


class FolderDetailSchemaOut(GroupPermissionReadOutMixin, TimestampMixin, Schema):
    id: int
    name: str
    description: str | None
    child_folders: list[RootFolderSchemaOut]
    folder_images: list[int]
    breadcrumbs: list[BreadcrumbSchema]
    has_children: bool


class FolderUpdateSchemaIn(GroupPermissionUpdateInMixin, Schema):
    name: str | None = None
    description: str | None = None
