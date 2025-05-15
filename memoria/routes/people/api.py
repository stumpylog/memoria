import logging

from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import LimitOffsetPagination
from ninja.pagination import paginate

from memoria.models import Person
from memoria.models import PersonInImage
from memoria.models.abstract import PermittedQueryset
from memoria.routes.people.schemas import PersonDetailOutSchema
from memoria.routes.people.schemas import PersonImageOutSchema
from memoria.routes.people.schemas import PersonReadOutSchema
from memoria.routes.people.schemas import PersonUpdateInSchema

router = Router(tags=["people"])

logger = logging.getLogger(__name__)


@router.get("/", response=list[PersonReadOutSchema], operation_id="get_all_people")
@paginate(LimitOffsetPagination)
def get_all_people(
    request: HttpRequest,
):
    user = request.user
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(user)

    permitted_people_queryset = Person.objects.permitted(user)

    return permitted_people_queryset.annotate(
        image_count=Count("images_featured_in", filter=permitted_image_filter),
    ).order_by("name")


@router.get("/{person_id}/", response=PersonDetailOutSchema, operation_id="get_person_detail")
def get_person_detail(
    request: HttpRequest,
    person_id: int,
):
    person: Person = get_object_or_404(Person.objects.permitted(request.user).with_images(), pk=person_id)
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(request.user)

    person_images = person.images_featured_in.filter(permitted_image_filter).distinct()

    logger.info(f"{person.name} has {person_images.count()} images")

    return {
        "id": person.pk,
        "name": person.name,
        "description": person.description,
        "image_count": person_images.count(),
    }


@router.get("/{person_id}/images/", response=list[PersonImageOutSchema], operation_id="get_person_images")
@paginate(LimitOffsetPagination)
def get_person_images(
    request: HttpRequest,
    person_id: int,
):
    person: Person = get_object_or_404(Person.objects.permitted(request.user).with_images(), pk=person_id)
    permitted_image_filter = PermittedQueryset.get_permitted_filter_q(request.user)

    return person.images_featured_in.filter(permitted_image_filter).distinct().order_by("-created_at")


@router.patch("/{person_id}/", response=PersonDetailOutSchema, operation_id="update_person_detail")
def update_person(request: HttpRequest, person_id: int, data: PersonUpdateInSchema):
    person_to_update: Person = get_object_or_404(Person.objects.permitted(request.user), pk=person_id)

    if data.name:
        existing_person = Person.objects.filter(name=data.name)
        if existing_person.exists():
            old_person_in_images = PersonInImage.objects.filter(person=person_to_update)

            # Handle the M2M relationship with Image through PersonInImage
            for person_in_image in old_person_in_images:
                image = person_in_image.image

                # Check if the image already has a relationship with the target person
                existing_relation = PersonInImage.objects.filter(
                    image=image,
                    person=existing_person,
                ).first()

                if existing_relation:
                    # If relationship exists, we can transfer any unique data or just delete
                    # For example: existing_relation.some_field = person_in_image.some_field
                    person_in_image.delete()
                else:
                    # If no relationship exists, update person reference to the target person
                    person_in_image.person = existing_person
                    person_in_image.save()
            person_to_update.delete()
            return existing_person
        person_to_update.name = data.name

    if data.description:
        person_to_update.description = data.description

    person_to_update.save()

    return person_to_update
