from datetime import datetime

from ninja import Schema
from pydantic import Field


class IdMixin(Schema):
    """
    Mixin for models that have an 'id' integer field.
    """

    id: int = Field(description="The unique identifier of the object")


class TimestampMixin(Schema):
    """
    Mixin for models that have 'created_at' and 'updated_at' fields.
    """

    created_at: datetime = Field(description="Timestamp when the object was created")
    updated_at: datetime = Field(description="Timestamp when the object was last updated")


class GroupSchemaOut(IdMixin, Schema):
    name: str = Field(description="The name of the group")


class GroupPermissionReadOutMixin(Schema):
    """
    Mixin for objects that have associated view and edit groups.
    Assumes GroupSchema is defined elsewhere (e.g., in this file or imported).
    """

    view_groups: list[GroupSchemaOut] = Field(
        default_factory=list,
        description="Groups allowed to view this object",
    )
    edit_groups: list[GroupSchemaOut] = Field(
        default_factory=list,
        description="Groups allowed to edit this object",
    )


class GroupPermissionUpdateInMixin(Schema):
    """
    Mixin for updating group permissions by IDs.
    """

    view_group_ids: list[int] | None = Field(
        default=None,
        description="New list of Group IDs allowed to view",
    )
    edit_group_ids: list[int] | None = Field(
        default=None,
        description="New list of Group IDs allowed to edit",
    )
