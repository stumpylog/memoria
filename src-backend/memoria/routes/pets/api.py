import logging
from http import HTTPStatus
from typing import Literal

from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404
from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router
from ninja.pagination import LimitOffsetPagination
from ninja.pagination import paginate

from memoria.common.auth import active_user_auth
from memoria.common.auth import async_active_user_auth
from memoria.models import Pet
from memoria.models.abstract import PermittedQueryset
from memoria.routes.pets.schemas import PetImageOutSchema
from memoria.routes.pets.schemas import PetReadDetailSchemaOut
from memoria.routes.pets.schemas import PetReadSchemaOut
from memoria.routes.pets.schemas import PetTypeChoices
from memoria.routes.pets.schemas import PetUpdateInSchema

router = Router(tags=["pets"])

logger = logging.getLogger(__name__)


def _get_pet_with_counts(pet_id: int, user) -> Pet:
    """
    Helper function to get pet with annotated counts
    """
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(user)
    return get_object_or_404(
        Pet.objects.prefetch_related("view_groups", "edit_groups").annotate(
            image_count=Count(
                "images_featured_in",
                filter=permitted_image_filter,
                distinct=True,
            ),
        ),
        pk=pet_id,
    )


async def _aget_pet_with_counts(pet_id: int, user) -> Pet:
    """
    Helper function to get pet with annotated counts
    """
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(user)
    return await aget_object_or_404(
        Pet.objects.prefetch_related("view_groups", "edit_groups").annotate(
            image_count=Count(
                "images_featured_in",
                filter=permitted_image_filter,
                distinct=True,
            ),
        ),
        pk=pet_id,
    )


@router.get("/", response=list[PetReadSchemaOut], operation_id="get_all_pets", auth=active_user_auth)
@paginate(LimitOffsetPagination)
def get_all_pets(
    request: HttpRequest,
    sort_by: Literal["name", "-name", "image_count", "-image_count"] = Query(
        "name",
        description="Field to sort by: 'name' or 'image_count'. "
        "Prefix with '-' for descending order (e.g., '-image_count').",
    ),
    pet_name: str | None = None,
    pet_type: PetTypeChoices | None = None,
):
    user = request.user
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(user)

    permitted_pet_filter = Pet.objects.permitted(user).with_images()

    if pet_name is not None:
        permitted_pet_filter = permitted_pet_filter.filter(name__icontains=pet_name)

    if pet_type is not None:
        permitted_pet_filter = permitted_pet_filter.filter(pet_type=pet_type)

    return permitted_pet_filter.annotate(
        image_count=Count("images_featured_in", filter=permitted_image_filter),
    ).order_by(sort_by)


@router.get(
    "/{pet_id}/",
    response=PetReadDetailSchemaOut,
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="get_pet_detail",
    auth=async_active_user_auth,
)
async def get_single_pet(
    request: HttpRequest,
    pet_id: int,
):
    return await _aget_pet_with_counts(pet_id, request.user)


@router.get(
    "/{pet_id}/images/",
    response=list[PetImageOutSchema],
    operation_id="get_pet_images",
    auth=active_user_auth,
)
@paginate(LimitOffsetPagination)
def get_person_images(
    request: HttpRequest,
    pet_id: int,
):
    pet: Pet = get_object_or_404(Pet.objects.permitted(request.user).with_images(), pk=pet_id)
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(request.user)

    return pet.images_featured_in.filter(permitted_image_filter).distinct().order_by("-created_at")


@router.patch(
    "/{pet_id}/",
    response={HTTPStatus.OK: PetReadDetailSchemaOut},
    openapi_extra={
        "responses": {
            HTTPStatus.NOT_FOUND: {
                "description": "Not Found Response",
            },
        },
    },
    operation_id="update_pet",
    auth=async_active_user_auth,
)
async def update_pet(
    request: HttpRequest,
    pet_id: int,
    data: PetUpdateInSchema,
):
    pet_to_update: Pet = await aget_object_or_404(
        Pet.objects.editable_by(request.user),
        pk=pet_id,
    )

    if data.name is not None:
        pet_to_update.name = data.name

    if data.description is not None:
        pet_to_update.description = data.description
    elif pet_to_update.description is not None:
        pet_to_update.description = None

    if data.pet_type is not None:
        pet_to_update.pet_type = data.pet_type

    await pet_to_update.asave()
    return await _aget_pet_with_counts(pet_id, request.user)
