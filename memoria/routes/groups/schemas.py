from ninja import Schema


class GroupCreateInSchema(Schema):
    name: str


class GroupOutSchema(Schema):
    id: int
    name: str


class GroupUpdateInSchema(Schema):
    name: str
