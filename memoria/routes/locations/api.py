import logging
from typing import cast

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


@router.get("/countries/", response=list[CountryListItemSchemaOut], operation_id="location_get_countries")
def get_all_countries(
    request: HttpRequest,  # noqa: ARG001
):
    return ALPHA2_CODE_TO_COUNTRIES.values()


@router.get("/subdivisions/", response=list[SubdivisionListItemSchemaOut], operation_id="location_get_subdivisions")
def get_subdivisions_for_country(
    request: HttpRequest,  # noqa: ARG001
    country_code: str,
):
    country = ALPHA2_CODE_TO_COUNTRIES.get(cast("CountryCodeAlpha2Type", country_code))
    if not country:
        raise HttpBadRequestError(f"There is no country {country_code}")
    return country.subdivisions


@router.get("/cities/", response=list[str], operation_id="location_get_cities")
def get_existing_cities(
    request: HttpRequest,
    country_code: str,
    subdivision_code: str,
):
    country = ALPHA2_CODE_TO_COUNTRIES.get(cast("CountryCodeAlpha2Type", country_code))
    if not country:
        raise HttpBadRequestError(f"There is no country {country_code}")
    if not country.contains_subdivision(subdivision_code):
        raise HttpBadRequestError(f"There is no {subdivision_code} in country{country_code}")
    return (
        RoughLocation.objects.permitted(request.user)
        .filter(
            country_code=country_code,
            subdivision_code=subdivision_code,
        )
        .values_list("city", flat=True)
    )


@router.get("/sublocations/", response=list[str], operation_id="location_get_sub_locations")
def get_existing_sublocations(
    request: HttpRequest,
    country_code: str,
    subdivision_code: str,
    city_name: str,
):
    country = ALPHA2_CODE_TO_COUNTRIES.get(cast("CountryCodeAlpha2Type", country_code))
    if not country:
        raise HttpBadRequestError(f"There is no country {country_code}")
    if not country.contains_subdivision(subdivision_code):
        raise HttpBadRequestError(f"There is no {subdivision_code} in country{country_code}")
    return (
        RoughLocation.objects.permitted(request.user)
        .filter(
            country_code=country_code,
            subdivision_code=subdivision_code,
            city__iexact=city_name,
        )
        .values_list("sub_location", flat=True)
    )
