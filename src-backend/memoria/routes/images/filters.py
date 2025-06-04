import logging
from datetime import date

from django.db.models import Q
from ninja import Field
from ninja import FilterSchema
from pydantic import model_validator

logger = logging.getLogger(__name__)


class ImageBooleanFilterSchema(FilterSchema):
    is_dirty: bool | None = Field(None, description="Filter by dirty status")
    is_starred: bool | None = Field(None, description="Filter by starred status")
    is_deleted: bool | None = Field(None, description="Filter by deletion status")

    def filter_queryset(self, queryset):
        if self.is_dirty is not None:
            queryset = queryset.filter(is_dirty=self.is_dirty)

        if self.is_starred is not None:
            queryset = queryset.filter(is_starred=self.is_starred)

        if self.is_deleted is not None:
            if self.is_deleted:
                queryset = queryset.exclude(deleted_at__isnull=True)
            else:
                queryset = queryset.filter(deleted_at__isnull=True)

        return queryset


class ImageFKFilterSchema(FilterSchema):
    folder_id: int | None = Field(None, description="Filter by ImageFolder ID")

    def filter_queryset(self, queryset):
        if self.folder_id is not None:
            queryset = queryset.filter(folder_id=self.folder_id)

        return queryset


class ImageM2MFilterSchema(FilterSchema):
    people_ids: list[int] | None = Field(None, description="Filter by Person IDs")
    pets_ids: list[int] | None = Field(None, description="Filter by Pet IDs")
    tags_ids: list[int] | None = Field(None, description="Filter by Tag IDs")
    exclude_people_ids: list[int] | None = Field(None, description="Exclude images with these Person IDs")
    exclude_pets_ids: list[int] | None = Field(None, description="Exclude images with these Pet IDs")
    exclude_tags_ids: list[int] | None = Field(None, description="Exclude images with these Tag IDs")
    require_all: bool = Field(False, description="Require ALL specified IDs to be present (AND logic)")

    def filter_queryset(self, queryset):
        if self.require_all:
            # AND logic: images must have ALL specified items
            if self.people_ids:
                for person_id in self.people_ids:
                    queryset = queryset.filter(people__id=person_id)

            if self.pets_ids:
                for pet_id in self.pets_ids:
                    queryset = queryset.filter(pets__id=pet_id)

            if self.tags_ids:
                for tag_id in self.tags_ids:
                    queryset = queryset.filter(tags__id=tag_id)
        else:
            # OR logic: original behavior - images with ANY specified items
            if self.people_ids:
                queryset = queryset.filter(people__id__in=self.people_ids).distinct()
            if self.pets_ids:
                queryset = queryset.filter(pets__id__in=self.pets_ids).distinct()
            if self.tags_ids:
                queryset = queryset.filter(tags__id__in=self.tags_ids).distinct()

        # Exclusion filters (always applied)
        if self.exclude_people_ids:
            queryset = queryset.exclude(people__id__in=self.exclude_people_ids)
        if self.exclude_pets_ids:
            queryset = queryset.exclude(pets__id__in=self.exclude_pets_ids)
        if self.exclude_tags_ids:
            queryset = queryset.exclude(tags__id__in=self.exclude_tags_ids)

        return queryset.distinct()


class ImageLocationFilterSchema(FilterSchema):
    country_code: str | None = Field(None, description="Filter by country code (ISO 3166-1 alpha 2)")
    subdivision_code: str | None = Field(None, description="Filter by state/province code (ISO 3166-2)")
    city: str | None = Field(None, description="Filter by city name (partial match)")
    sub_location: str | None = Field(None, description="Filter by sub-location (partial match)")

    def filter_queryset(self, queryset):
        if self.country_code is not None:
            queryset = queryset.filter(location__country_code=self.country_code)

        if self.subdivision_code is not None:
            queryset = queryset.filter(location__subdivision_code=self.subdivision_code)

        if self.city is not None:
            queryset = queryset.filter(location__city__icontains=self.city)

        if self.sub_location is not None:
            queryset = queryset.filter(location__sub_location__icontains=self.sub_location)

        return queryset


class ImageDateFilterSchema(FilterSchema):
    date_start: date | None = Field(None, description="Filter images from this date onwards using comparison_date")
    date_end: date | None = Field(None, description="Filter images up to this date using comparison_date")
    year_start: int | None = Field(None, description="Filter images from this year onwards")
    year_end: int | None = Field(None, description="Filter images up to this year")
    month_start: int | None = Field(
        None,
        description="Filter images from this month onwards (1-12, includes null months)",
    )
    month_end: int | None = Field(None, description="Filter images up to this month (1-12, includes null months)")
    day_start: int | None = Field(None, description="Filter images from this day onwards (1-31, includes null days)")
    day_end: int | None = Field(None, description="Filter images up to this day (1-31, includes null days)")

    @model_validator(mode="after")
    def validate_date_hierarchy(self):
        # Day filters require month filters
        # Month filters require year filters
        if self.day_start is not None and self.month_start is None:
            raise ValueError("Starting day filter is missing a starting month")  # noqa: EM101, TRY003
        if self.month_start is not None and self.year_start is None:
            raise ValueError("Starting month filter is missing a starting year value")  # noqa: EM101, TRY003

        if self.date_end is not None and self.month_end is None:
            raise ValueError("Ending day filter is missing an ending month")  # noqa: EM101, TRY003
        if self.month_end is not None and self.year_end is None:
            raise ValueError("Ending month filter is missing an ending year value")  # noqa: EM101, TRY003
        return self

    def filter_queryset(self, queryset):
        filters = Q()

        # Use comparison_date for precise date range filtering
        if self.date_start is not None:
            filters &= Q(date__comparison_date__gte=self.date_start)
        if self.date_end is not None:
            filters &= Q(date__comparison_date__lte=self.date_end)

        # Individual field filtering for more granular control
        if self.year_start is not None:
            filters &= Q(date__year__gte=self.year_start)
        if self.year_end is not None:
            filters &= Q(date__year__lte=self.year_end)

        # For month/day, include nulls to match "incomplete" dates
        if self.year_start:
            filters &= Q(date__year__gte=self.year_start)
        if self.year_end:
            filters &= Q(year__lte=self.year_end)
        if self.month_start:
            filters &= Q(date__month__gte=self.month_start)
        if self.month_end:
            filters &= Q(date__month__lte=self.month_end)
        if self.day_start:
            filters &= Q(date__day__gte=self.day_start)
        if self.day_end:
            filters &= Q(date__day__lte=self.day_end)

        return queryset.filter(filters)


class ImageExactDateFilterSchema(FilterSchema):
    """Exact matching for specific year/month/day combinations"""

    year: int | None = Field(None, description="Filter images from this exact year")
    month: int | None = Field(None, ge=1, le=12, description="Filter images from this exact month (1-12)")
    day: int | None = Field(None, ge=1, le=31, description="Filter images from this exact day (1-31)")

    @model_validator(mode="after")
    def validate_date_hierarchy(self):
        if self.day is not None and self.month is None:
            raise ValueError("Day filter requires month to be specified")
        if self.month is not None and self.year is None:
            raise ValueError("Month filter requires year to be specified")
        return self

    def filter_queryset(self, queryset):
        filters = Q()

        if self.year is not None:
            filters &= Q(date__year=self.year)

        if self.month is not None:
            filters &= Q(date__month=self.month)

        if self.day is not None:
            filters &= Q(date__day=self.day)

        return queryset.filter(filters)
