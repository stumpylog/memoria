from simpleiso3166.countries.data import ALPHA2_CODE_TO_COUNTRIES
from simpleiso3166.countries.types import CountryCodeAlpha2Type


def get_country_list_for_autocomplete() -> list[dict[str, str]]:
    """
    Returns a list of countries formatted for Choices.js.
    """
    return [{"value": code, "label": data.common_name or data.name} for code, data in ALPHA2_CODE_TO_COUNTRIES.items()]


def get_subdivisions_for_country_for_autocomplete(country_code: CountryCodeAlpha2Type) -> list[dict[str, str]]:
    """
    Returns a list of subdivisions for a given country, formatted for Choices.js.
    """
    country_data = ALPHA2_CODE_TO_COUNTRIES.get(country_code)
    if country_data:
        return [{"value": subdivision.code, "label": subdivision.name} for subdivision in country_data.subdivisions]
    return []
