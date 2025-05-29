import logging
from typing import Literal

from django.db import transaction
from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router
from ninja.pagination import LimitOffsetPagination
from ninja.pagination import paginate

from memoria.common.auth import active_user_auth
from memoria.models import Person
from memoria.models import PersonInImage
from memoria.models.abstract import PermittedQueryset
from memoria.routes.people.schemas import PersonDetailOutSchema
from memoria.routes.people.schemas import PersonImageOutSchema
from memoria.routes.people.schemas import PersonReadOutSchema
from memoria.routes.people.schemas import PersonUpdateInSchema

router = Router(tags=["people"])

logger = logging.getLogger(__name__)


def _get_person_with_counts(person_id: int, user) -> Person:
    """
    Helper function to get person with annotated counts
    """
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(user)
    return get_object_or_404(
        Person.objects.prefetch_related("view_groups", "edit_groups").annotate(
            image_count=Count(
                "images_featured_in",
                filter=permitted_image_filter,
                distinct=True,
            ),
        ),
        pk=person_id,
    )


@router.get("/", response=list[PersonReadOutSchema], operation_id="get_all_people", auth=active_user_auth)
@paginate(LimitOffsetPagination)
def get_all_people(
    request: HttpRequest,
    sort_by: Literal["name", "-name", "image_count", "-image_count"] = Query(
        "name",
        description="Field to sort by: 'name' or 'image_count'. "
        "Prefix with '-' for descending order (e.g., '-image_count').",
    ),
    person_name: str | None = None,
):
    user = request.user
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(user)

    permitted_people_queryset = Person.objects.permitted(user).with_images()

    if person_name is not None:
        permitted_people_queryset = permitted_people_queryset.filter(name__icontains=person_name)

    return permitted_people_queryset.annotate(
        image_count=Count("images_featured_in", filter=permitted_image_filter),
    ).order_by(sort_by)


@router.get("/{person_id}/", response=PersonDetailOutSchema, operation_id="get_person_detail", auth=active_user_auth)
def get_person_detail(
    request: HttpRequest,
    person_id: int,
):
    return _get_person_with_counts(person_id, request.user)


@router.get(
    "/{person_id}/images/",
    response=list[PersonImageOutSchema],
    operation_id="get_person_images",
    auth=active_user_auth,
)
@paginate(LimitOffsetPagination)
def get_person_images(
    request: HttpRequest,
    person_id: int,
):
    person: Person = get_object_or_404(Person.objects.permitted(request.user).with_images(), pk=person_id)
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(request.user)

    return person.images_featured_in.filter(permitted_image_filter).distinct().order_by("-created_at")


@router.patch(
    "/{person_id}/",
    response=PersonDetailOutSchema,
    operation_id="update_person_detail",
    auth=active_user_auth,
)
def update_person(request: HttpRequest, person_id: int, data: PersonUpdateInSchema):
    person_to_update: Person = get_object_or_404(
        Person.objects.editable_by(request.user),
        pk=person_id,
    )

    if data.name:
        existing_person = Person.objects.filter(name=data.name).first()
        if existing_person is not None:
            with transaction.atomic():
                logger.warning(f"Person {data.name} already exists, merging")

                # Alternative: Ultra-optimized database-only approach
                # Delete duplicates first
                PersonInImage.objects.filter(
                    person=person_to_update,
                    image__in=PersonInImage.objects.filter(person=existing_person).values("image"),
                ).delete()

                # Update remaining relationships in one query
                PersonInImage.objects.filter(person=person_to_update).update(person=existing_person)

                person_to_update.delete()

                # Return the existing person with counts
                return _get_person_with_counts(existing_person.pk, request.user)

        person_to_update.name = data.name

    # Handle description update
    if data.description is not None:
        person_to_update.description = data.description
    elif person_to_update.description is not None:
        person_to_update.description = None

    # Handle group updates
    if data.view_group_ids:
        person_to_update.view_groups.set(data.view_group_ids)
    if data.edit_group_ids:
        person_to_update.edit_groups.set(data.edit_group_ids)

    person_to_update.save()

    # Return the updated person with counts
    return _get_person_with_counts(person_to_update.pk, request.user)
