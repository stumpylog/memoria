import logging
from http import HTTPStatus

from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Router
from ninja.pagination import PageNumberPagination
from ninja.pagination import paginate
from scansteward.common.errors import HttpConflictError
from scansteward.models import Person
from scansteward.routes.people.schemas import PersonCreateInSchema
from scansteward.routes.people.schemas import PersonReadOutSchema
from scansteward.routes.people.schemas import PersonUpdateInSchema

router = Router(tags=["people"])

logger = logging.getLogger(__name__)


@router.get("/", response=list[PersonReadOutSchema], operation_id="get_people")
@paginate(PageNumberPagination)
def get_all_people(
    request: HttpRequest,  # noqa: ARG001
    name_like: str | None = None,
):
    qs = Person.objects.all()
    if name_like is not None:
        qs = qs.filter(name__icontains=name_like)

    return qs


@router.get(
    "/{person_id}/",
    response=PersonReadOutSchema,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_person",
)
async def get_single_person(
    request: HttpRequest,  # noqa: ARG001
    person_id: int,
):
    instance: Person = await aget_object_or_404(Person, id=person_id)
    return instance


@router.post(
    "/",
    response={HTTPStatus.CREATED: PersonReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
            HTTPStatus.BAD_REQUEST: {
                "description": "Person Already Exists",
            },
        },
    },
    operation_id="create_person",
)
async def create_person(
    request: HttpRequest,  # noqa: ARG001
    data: PersonCreateInSchema,
):
    person_name_exists = await Person.objects.filter(name__iexact=data.name).aexists()
    if person_name_exists:
        msg = f"Person named {data.name} already exists"
        logger.error(msg)
        raise HttpConflictError(msg)
    instance: Person = await Person.objects.acreate(
        name=data.name,
        description=data.description,
    )
    return HTTPStatus.CREATED, instance


@router.patch(
    "/{person_id}/",
    response={HTTPStatus.OK: PersonReadOutSchema},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_person",
)
async def update_person(
    request: HttpRequest,  # noqa: ARG001
    person_id: int,
    data: PersonUpdateInSchema,
):
    instance: Person = await aget_object_or_404(Person, id=person_id)
    if data.name is not None:
        instance.name = data.name
    if data.description is not None:
        instance.description = data.description
    await instance.asave()
    await instance.arefresh_from_db()
    return instance


@router.delete(
    "/{person_id}/",
    response={HTTPStatus.NO_CONTENT: None},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="delete_person",
)
async def delete_person(
    request: HttpRequest,  # noqa: ARG001
    person_id: int,
):
    instance: Person = await aget_object_or_404(Person, id=person_id)
    await instance.adelete()
    return HTTPStatus.NO_CONTENT, None
