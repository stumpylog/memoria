from __future__ import annotations

import sys

from ninja import Field
from ninja import Schema
from pydantic import model_validator

from memoria.utils.geo import subdivision_in_country

if sys.version_info > (3, 11):
    from typing import Self
else:
    from typing import Self


class CountryListItemSchemaOut(Schema):
    alpha2: str
    best_name: str


class SubdivisionListItemSchemaOut(Schema):
    code: str
    name: str


class LocationCreateInSchema(Schema):
    """
    Schema to create a Location
    """

    country_code: str = Field(
        description="The ISO 3166-1 alpha-2 code of the country",
    )
    subdivision_code: str | None = Field(
        default=None,
        description="The ISO 3166-2 subdivision code of the location",
    )
    city: str | None = Field(default=None, description="The city of the location")
    sub_location: str | None = Field(
        default=None,
        description="The location taken or shown",
    )


class LocationReadOutSchema(LocationCreateInSchema):
    """
    Schema to create a Location
    """

    id: int = Field(description="The id of the location")


class LocationUpdateInSchema(Schema):
    """
    Schema to create a Location
    """

    country_code: str | None = Field(
        default=None,
        description="The new ISO 3166-1 alpha-2 code of the country",
    )
    subdivision_code: str | None = Field(
        default=None,
        description="The new ISO 3166-2 subdivision code of the location",
    )
    city: str | None = Field(default=None, description="The new city of the location")
    sub_location: str | None = Field(
        default=None,
        description="The new location taken or shown",
    )

    @model_validator(mode="after")
    def check_country_with_subdivision(self) -> Self:
        if self.subdivision_code and not self.country_code:
            msg = "Subdivision must also include country code"
            raise ValueError(msg)
        if (
            self.country_code
            and self.subdivision_code
            and not subdivision_in_country(self.country_code, self.subdivision_code)
        ):
            msg = f"{self.subdivision_code} is not a valid subdivision of {self.country_code}"
            raise ValueError(msg)
        return self
