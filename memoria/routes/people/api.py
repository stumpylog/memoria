import logging

from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from memoria.models import Person
from memoria.models.abstract import PermittedQueryset
from memoria.routes.people.schemas import PersonDetailOutSchema
from memoria.routes.people.schemas import PersonReadOutSchema

router = Router(tags=["people"])

logger = logging.getLogger(__name__)


@router.get("/", response=list[PersonReadOutSchema], operation_id="get_all_people")
def get_all_people(
    request: HttpRequest,
):
    user = request.user
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(user)

    permitted_people_queryset = Person.objects.permitted(user)

    return permitted_people_queryset.annotate(
        image_count=Count("images_featured_in", filter=permitted_image_filter),
    )


@router.get("/{person_id}/", response=PersonDetailOutSchema, operation_id="get_person_detail")
def get_person_detail(
    request: HttpRequest,
    person_id: int,
):
    person: Person = get_object_or_404(Person.objects.permitted(request.user).with_images(), pk=person_id)
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(request.user)

    logger.info(f"{person.name} has {person.images_featured_in.count()} images")

    return {
        "id": person.pk,
        "name": person.name,
        "description": person.description,
        "image_ids": person.images_featured_in.filter(permitted_image_filter).distinct().values_list("pk", flat=True),
    }
