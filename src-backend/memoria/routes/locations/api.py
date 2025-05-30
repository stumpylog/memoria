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
        msg = f"There is no country {country_code}"
        logger.error(msg)
        raise HttpBadRequestError(msg)
    return country.subdivisions


@router.get("/cities/", response=list[str], operation_id="location_get_cities")
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
    return list(
        RoughLocation.objects.filter(
            country_code=country_code,
            subdivision_code=subdivision_code,
            city__isnull=False,
        ).values_list("city", flat=True),
    )


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
    return list(
        RoughLocation.objects.filter(
            country_code=country_code,
            subdivision_code=subdivision_code,
            city__icontains=city_name,
            sub_location__isnull=False,
        )
        .all()
        .values_list("sub_location", flat=True),
    )
