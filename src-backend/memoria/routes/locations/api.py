import logging
from typing import cast

from django.db.models import Count
from django.http import HttpRequest
from ninja import Router
from simpleiso3166 import ALPHA2_CODE_TO_COUNTRIES
from simpleiso3166 import CountryCodeAlpha2Type

from memoria.common.errors import HttpBadRequestError
from memoria.models import RoughLocation
from memoria.routes.locations.schemas import CountryListItemSchemaOut
from memoria.routes.locations.schemas import SubdivisionListItemSchemaOut

router = Router(tags=["locations"])

logger = logging.getLogger(__name__)


@router.get(
    "/countries/all/",
    response=list[CountryListItemSchemaOut],
    operation_id="list_all_world_countries",
    description="List all countries in the world, as per ISO-3166-1",
)
def get_all_countries(
    request: HttpRequest,  # noqa: ARG001
):
    return ALPHA2_CODE_TO_COUNTRIES.values()


@router.get(
    "/countries/",
    response=list[CountryListItemSchemaOut],
    operation_id="list_countries",
    description="List all countries where images have been taken",
)
def get_countries_with_images_in_them(
    request: HttpRequest,  # noqa: ARG001
):
    rough_locations_with_images = (
        RoughLocation.objects.annotate(
            num_images=Count("images"),
        )
        .filter(images__isnull=False, num_images__gt=0)
        .order_by("country_code")
    )
    data: list[CountryListItemSchemaOut] = []
    seen = set()
    for location in rough_locations_with_images:
        if location.country_code not in seen:
            data.append(
                CountryListItemSchemaOut(
                    alpha2=location.country_code,
                    best_name=ALPHA2_CODE_TO_COUNTRIES[location.country_code].best_name,
                ),
            )
            seen.add(location.country_code)
    return sorted(data, key=lambda x: x.best_name)


@router.get(
    "/subdivisions/all/",
    response=list[SubdivisionListItemSchemaOut],
    operation_id="list_all_country_subdivisions",
    description="List all subdivisions of a given country, as per ISO-3166-2",
)
def get_subdivisions_for_country(
    request: HttpRequest,  # noqa: ARG001
    country_code: str,
):
    country = ALPHA2_CODE_TO_COUNTRIES.get(cast("CountryCodeAlpha2Type", country_code))
    if not country:
        msg = f"There is no country {country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)
    return country.subdivisions


@router.get(
    "/subdivisions/",
    response=list[SubdivisionListItemSchemaOut],
    operation_id="list_subdivisions",
    description="List all subdivisions/states where images have been taken, filtered by country code",
)
def get_subdivisions_with_images_in_them(
    request: HttpRequest,  # noqa: ARG001
    country_code: str,
):
    country = ALPHA2_CODE_TO_COUNTRIES.get(cast("CountryCodeAlpha2Type", country_code))

    if not country:
        msg = f"There is no country {country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)

    # Get distinct subdivision codes from RoughLocation objects that have images
    # We still need to count images to filter, but we then care about distinct subdivision codes.
    # We are selecting only the 'subdivision_code' field from the database.
    distinct_subdivision_codes_qs = (
        RoughLocation.objects.filter(
            country_code=country_code,
            subdivision_code__isnull=False,
            images__isnull=False,  # Ensure there's at least one image associated
        )
        .values_list("subdivision_code", flat=True)
        .distinct()
        .order_by("subdivision_code")
    )

    # Convert the QuerySet to a list of strings
    subdivision_codes = list(distinct_subdivision_codes_qs)

    result: list[SubdivisionListItemSchemaOut] = []
    for code in subdivision_codes:
        subdivision_obj = country.get_subdivision(code)
        if subdivision_obj:  # Ensure subdivision object exists
            result.append(
                SubdivisionListItemSchemaOut(
                    code=code,
                    name=subdivision_obj.name,
                ),
            )
    return sorted(result, key=lambda x: x.name)


@router.get("/cities/", response=list[str], operation_id="list_possible_country_cities")
def get_existing_cities(
    request: HttpRequest,  # noqa: ARG001
    country_code: str,
    subdivision_code: str | None = None,
):
    country = ALPHA2_CODE_TO_COUNTRIES.get(cast("CountryCodeAlpha2Type", country_code))
    if not country:
        msg = f"There is no country {country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)
    if subdivision_code is not None and not country.contains_subdivision(subdivision_code):
        msg = f"There is no {subdivision_code} in country {country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)
    qs = RoughLocation.objects.filter(country_code=country_code, city__isnull=False)
    if subdivision_code is not None:
        qs = qs.filter(subdivision_code=subdivision_code)
    return qs.values_list("city", flat=True).distinct().order_by("city")


@router.get("/sublocations/", response=list[str], operation_id="location_get_sub_locations")
def get_existing_sublocations(
    request: HttpRequest,  # noqa: ARG001
    country_code: str,
    city_name: str,
    subdivision_code: str | None = None,
):
    country = ALPHA2_CODE_TO_COUNTRIES.get(cast("CountryCodeAlpha2Type", country_code))
    if not country:
        msg = f"There is no country {country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)
    if subdivision_code is not None and not country.contains_subdivision(subdivision_code):
        msg = f"There is no {subdivision_code} in country {country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)
    qs = RoughLocation.objects.filter(country_code=country_code, city__icontains=city_name, sub_location__isnull=False)
    if subdivision_code is not None:
        qs = qs.filter(subdivision_code=subdivision_code)

    return qs.values_list("sub_location", flat=True).distinct().order_by("sub_location")
