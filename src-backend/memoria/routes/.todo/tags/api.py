from http import HTTPStatus

from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Query
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination
from ninja.pagination import paginate

from memoria.models import Tag
from memoria.routes.tags.schemas import TagCreateInSchema
from memoria.routes.tags.schemas import TagNameFilter
from memoria.routes.tags.schemas import TagReadOutSchema
from memoria.routes.tags.schemas import TagTreeOutSchema
from memoria.routes.tags.schemas import TagUpdateInSchema

router = Router(tags=["tags"])


@router.get("/tree/", response=list[TagTreeOutSchema], operation_id="get_tag_tree")
def get_tag_tree(
    request: HttpRequest,  # noqa: ARG001
    filter_name_query: Query[TagNameFilter],
):
    items = []
    for root_node in (
        Tag.objects.filter(parent__isnull=True)
        .filter(filter_name_query.get_filter_expression())
        .order_by("name")
        .prefetch_related("children")
    ):
        tree_root = TagTreeOutSchema.from_orm(root_node)
        items.append(tree_root)
    return items


@router.get("/", response=list[TagReadOutSchema], operation_id="get_all_tags")
@paginate(PageNumberPagination)
def get_tags(
    request: HttpRequest,  # noqa: ARG001
):
    return Tag.objects.all()


@router.get(
    "/{tag_id}/",
    response=TagReadOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_single_tag",
)
async def get_single_tag(
    request: HttpRequest,  # noqa: ARG001
    tag_id: int,
):
    instance: Tag = await aget_object_or_404(Tag, id=tag_id)
    return instance


@router.post(
    "/",
    response={HTTPStatus.CREATED: TagReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.BAD_REQUEST: {
                "description": "Tag Already Exists",
            },
        },
    },
    operation_id="create_tag",
)
async def create_tag(
    request: HttpRequest,  # noqa: ARG001
    data: TagCreateInSchema,
):
    tag_name_exists = await Tag.objects.filter(name=data.name).aexists()
    if tag_name_exists:
        raise HttpError(
            HTTPStatus.BAD_REQUEST,
            f"Tag named {data.name} already exists",
        )
    parent: Tag | None = None
    if data.parent_id is not None:
        parent = await aget_object_or_404(Tag, id=data.parent_id)
    instance: Tag = await Tag.objects.acreate(
        name=data.name,
        description=data.description,
        parent=parent,
    )
    return HTTPStatus.CREATED, instance


@router.patch(
    "/{tag_id}/",
    response={HTTPStatus.OK: TagReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_tag",
)
async def update_tag(
    request: HttpRequest,  # noqa: ARG001
    tag_id: int,
    data: TagUpdateInSchema,
):
    instance: Tag = await aget_object_or_404(Tag, id=tag_id)
    if data.name is not None:
        instance.name = data.name
    if data.description is not None:
        instance.description = data.description
    if data.parent_id is not None:
        parent = await aget_object_or_404(Tag, id=data.parent_id)
        instance.parent = parent
    await instance.asave()
    await instance.arefresh_from_db()
    return instance


@router.delete(
    "/{tag_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_tag",
)
async def delete_tag(
    request: HttpRequest,  # noqa: ARG001
    tag_id: int,
):
    instance: Tag = await aget_object_or_404(Tag, id=tag_id)
    await instance.adelete()
    return HTTPStatus.NO_CONTENT, None
