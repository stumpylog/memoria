from functools import lru_cache

from simpleiso3166.countries import Country
from simpleiso3166.countries.types import CountryCodeAlpha2Type
from simpleiso3166.subdivisions.types import SubdivisionCodeType


@lru_cache
def subdivision_in_country(
    country_code: CountryCodeAlpha2Type,
    subdivision_code: SubdivisionCodeType,
) -> bool:
    """
    Returns True if the given country code and subdivision code are valid together.
    """
    country = Country.from_alpha2(country_code)
    if not country:
        return False
    return country.contains_subdivision(subdivision_code)


@lru_cache
def get_country_code_from_name(country_name: str) -> CountryCodeAlpha2Type | None:
    """
    Returns the code of the given country name, or None if the country is not valid.
    """
    if country_name.lower() in {"us", "usa", "united states"}:
        country_name = "United States of America"
    results = list(Country.from_partial_name(country_name))
    if results:
        return results[0].alpha2
    return None


@lru_cache
def get_subdivision_code_from_name(
    country_alpha2: CountryCodeAlpha2Type,
    subdivision_name: str,
) -> SubdivisionCodeType | None:
    """
    Returns the code of the given country name, or None if the country is not valid.
    """
    if subdivision_name.strip().lower() == "dc":
        subdivision_name = "District of Columbia"
    country = Country.from_alpha2(country_alpha2)
    if not country:
        return None
    for subdivision in country.subdivisions:
        if subdivision.name == subdivision_name:
            return subdivision.code
    return None
