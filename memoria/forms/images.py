# memoria/forms.py


import datetime
from typing import Any
from typing import cast

from django import forms
from simpleiso3166 import ALPHA2_CODE_TO_COUNTRIES
from simpleiso3166 import CountryCodeAlpha2Type

from memoria.models import Image
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.utils.geo import get_country_code_from_name
from memoria.utils.geo import get_subdivision_code_from_name
from memoria.utils.geo import subdivision_in_country


class ImageUpdateForm(forms.ModelForm):
    # Date fields
    date_year = forms.IntegerField(
        required=False,
        label="Year",
        widget=forms.NumberInput(attrs={"placeholder": "YYYY"}),
    )
    date_month = forms.IntegerField(
        required=False,
        label="Month",
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={"placeholder": "MM"}),
    )
    date_day = forms.IntegerField(
        required=False,
        label="Day",
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={"placeholder": "DD"}),
    )

    # Location fields - these are for user input and will be processed
    location_country_input = forms.CharField(
        required=False,
        label="Country (Name or ISO Code)",
        widget=forms.TextInput(attrs={"placeholder": "e.g., United States or US"}),
    )
    location_subdivision_input = forms.CharField(
        required=False,
        label="State/Province (Name or Code)",
        widget=forms.TextInput(attrs={"placeholder": "e.g., California or CA"}),
    )
    location_city = forms.CharField(
        max_length=255,
        required=False,
        label="City",
        widget=forms.TextInput(attrs={"placeholder": "e.g., San Francisco"}),
    )
    location_sub_location = forms.CharField(
        max_length=255,
        required=False,
        label="Sub Location / Address Detail",
        widget=forms.TextInput(attrs={"placeholder": "e.g., Golden Gate Bridge"}),
    )

    class Meta:
        model = Image
        fields = ["title", "description"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Populate custom date fields from Image.date (RoughDate instance)
            if self.instance.date:
                rough_date_obj: RoughDate = self.instance.date
                self.fields["date_year"].initial = rough_date_obj.date.year
                if rough_date_obj.month_valid:
                    self.fields["date_month"].initial = rough_date_obj.date.month
                    if rough_date_obj.day_valid:
                        self.fields["date_day"].initial = rough_date_obj.date.day

            # Populate custom location fields from Image.location (RoughLocation instance)
            if self.instance.location:
                loc: RoughLocation = self.instance.location
                self.fields[
                    "location_country_input"
                ].initial = loc.country_code  # Or fetch name: get_country_name_from_code(loc.country_code)
                self.fields["location_subdivision_input"].initial = loc.subdivision_code  # Or fetch name
                self.fields["location_city"].initial = loc.city
                self.fields["location_sub_location"].initial = loc.sub_location

    def clean(self) -> dict[str, Any]:
        cleaned_data: dict[str, Any] = super().clean()

        year: int | None = cleaned_data.get("date_year")
        month: int | None = cleaned_data.get("date_month")
        day: int | None = cleaned_data.get("date_day")

        # Date validation logic
        if day and not month:
            self.add_error("date_month", "Month is required if a day is specified.")
        if month and not year:
            self.add_error("date_year", "Year is required if a month is specified.")

        if year and month and day:
            try:
                datetime.date(year, month, day)
            except ValueError:
                self.add_error("date_day", f"Invalid day ({day}) for the selected month ({month}) and year ({year}).")

        # Location validation and normalization
        country_input: str = cleaned_data.get("location_country_input", "").strip()
        subdivision_input: str = cleaned_data.get("location_subdivision_input", "").strip()
        city: str | None = cleaned_data.get("location_city", "").strip()
        sub_location: str | None = cleaned_data.get("location_sub_location", "").strip()

        final_country_code: CountryCodeAlpha2Type | None = None
        if country_input:
            code_from_name = get_country_code_from_name(country_input)
            if code_from_name:
                final_country_code = code_from_name
            elif len(country_input) == 2 and country_input.isalpha():  # Basic check for code format
                if country_input.upper() in ALPHA2_CODE_TO_COUNTRIES:
                    final_country_code = cast("CountryCodeAlpha2Type", country_input.upper())
                else:
                    self.add_error(
                        "location_country_input",
                        "Invalid country name or code. Please use a recognized name or 2-letter ISO code.",
                    )
            else:
                self.add_error(
                    "location_country_input",
                    "Invalid country format. Use a recognized name or 2-letter ISO code.",
                )
        cleaned_data["final_country_code"] = final_country_code

        final_subdivision_code: str | None = None
        if final_country_code and subdivision_input:
            code_from_name = get_subdivision_code_from_name(final_country_code, subdivision_input)
            if code_from_name:
                final_subdivision_code = code_from_name
            # Check if input itself is a valid code part for the country
            elif subdivision_in_country(final_country_code, subdivision_input.upper()):
                final_subdivision_code = subdivision_input.upper()
            # Check if input was a full ISO 3166-2 code like "US-CA"
            elif "-" in subdivision_input and len(subdivision_input.split("-")) == 2:
                country_part, _ = subdivision_input.split("-", 1)
                if country_part.upper() == final_country_code and subdivision_in_country(
                    final_country_code,
                    subdivision_input.upper(),
                ):
                    final_subdivision_code = subdivision_input.upper()
                else:
                    self.add_error(
                        "location_subdivision_input",
                        f"Subdivision '{subdivision_input}' does not match country '{final_country_code}' or is invalid.",
                    )
            else:
                self.add_error(
                    "location_subdivision_input",
                    f"Invalid subdivision '{subdivision_input}' for country '{final_country_code}'. Use a recognized name or code.",
                )

        elif subdivision_input and not final_country_code:
            self.add_error("location_country_input", "A valid country is required if subdivision is specified.")
        cleaned_data["final_subdivision_code"] = final_subdivision_code

        # Dependency checks for city and sub_location
        if city and not final_country_code:
            self.add_error("location_country_input", "Country is required if city is specified.")
        if sub_location and not city:
            self.add_error("location_city", "City is required if sub-location is specified.")

        # Store processed city/sub_location for save method
        cleaned_data["processed_city"] = city if city else None
        cleaned_data["processed_sub_location"] = sub_location if sub_location else None

        return cleaned_data

    def save(self, commit: bool = True) -> Image:
        instance: Image = super().save(commit=False)

        # Handle RoughDate creation/retrieval
        year: int | None = self.cleaned_data.get("date_year")
        month: int | None = self.cleaned_data.get("date_month")
        day: int | None = self.cleaned_data.get("date_day")

        if year:
            month_is_valid: bool = bool(month)
            day_is_valid: bool = bool(day and month_is_valid)  # Day only valid if month is

            # Use 1st of month/year if month/day aren't specified, for DB date field
            effective_month: int = month if month_is_valid else 1
            effective_day: int = day if day_is_valid else 1

            try:
                # This date is what gets stored in RoughDate.date
                # The month_valid/day_valid flags indicate its precision.
                date_value_for_db: datetime.date = datetime.date(year, effective_month, effective_day)

                rough_date_obj, _ = RoughDate.objects.get_or_create(
                    date=date_value_for_db,
                    month_valid=month_is_valid,
                    day_valid=day_is_valid,
                )
                instance.date = rough_date_obj
            except ValueError:  # Should have been caught in clean(), but safeguard
                instance.date = None
        else:  # No year provided, so no date.
            instance.date = None

        # Handle RoughLocation creation/retrieval
        country_code_val: CountryCodeAlpha2Type | None = self.cleaned_data.get("final_country_code")
        subdivision_code_val: SubdivisionCodeType | None = self.cleaned_data.get("final_subdivision_code")
        city_val: str | None = self.cleaned_data.get("processed_city")
        sub_location_val: str | None = self.cleaned_data.get("processed_sub_location")

        if country_code_val:  # A country is the minimum requirement for a RoughLocation
            rough_loc_obj, _ = RoughLocation.objects.get_or_create(
                country_code=country_code_val,
                subdivision_code=subdivision_code_val,  # Will be None if not provided/valid
                city=city_val,  # Will be None if not provided
                sub_location=sub_location_val,  # Will be None if not provided
            )
            instance.location = rough_loc_obj
        else:  # No country, so no location.
            instance.location = None

        if commit:
            instance.save()
        return instance
