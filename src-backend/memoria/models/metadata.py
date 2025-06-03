from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from simpleiso3166 import Country
from treenode.models import TreeNodeModel

from memoria.models.abstract import AbstractBoxInImage
from memoria.models.abstract import AbstractSimpleNamedModelMixin
from memoria.models.abstract import AbstractTimestampMixin
from memoria.models.abstract import ObjectPermissionModelMixin
from memoria.models.abstract import PermittedQueryset

if TYPE_CHECKING:
    from collections.abc import Sequence

    from memoria.models.image import Image  # noqa: F401


class Tag(AbstractTimestampMixin, AbstractSimpleNamedModelMixin, TreeNodeModel):
    """
    Holds the information about a Tag, roughly a tag, in a tree structure,
    whose structure makes sense to the user
    """

    treenode_display_field = "name"

    name = models.CharField(max_length=100, db_index=True)

    description = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta(TreeNodeModel.Meta):
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self) -> str:
        return f"Tag {self.name}"

    def __repr__(self) -> str:
        return f"Tag: {self!s}"


class TagOnImage(models.Model):  # noqa: DJ008
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        help_text=_("Tag is on this Image"),
        related_name="image_links",
    )

    image = models.ForeignKey(
        "Image",
        on_delete=models.CASCADE,
        help_text=_("A Tag is on this Image"),
        related_name="applied_tags",
    )

    applied = models.BooleanField(default=False, help_text="This tag is applied to this image")


class PersonQuerySet(PermittedQueryset):
    def with_images(self) -> PersonQuerySet:
        """
        Fetches the person with Images
        """
        return self.prefetch_related(
            "images_featured_in",
        )


class Person(
    AbstractSimpleNamedModelMixin,
    AbstractTimestampMixin,
    ObjectPermissionModelMixin,
    models.Model,
):
    """
    Holds the information about a single person
    """

    objects: PersonQuerySet = PersonQuerySet.as_manager()

    def __str__(self) -> str:
        return f"Person {self.name}"


class PersonInImage(AbstractBoxInImage):
    person = models.ForeignKey(
        Person,
        # TODO: This would need to update if we allow boxes without a name/person attached
        on_delete=models.CASCADE,
        related_name="person_appearances",
        help_text=_("Person is in this Image at the given location"),
    )

    exclude_from_training = models.BooleanField(
        default=False,
        help_text=_("For future growth, do not use this box for facial recognition training"),
    )

    @property
    def name(self) -> str:
        if self.person:
            return self.person.name
        return "Unknown"


class PetQuerySet(PermittedQueryset):
    def with_images(self) -> PetQuerySet:
        """
        Fetches the pet with Images
        """
        return self.prefetch_related(
            "images_featured_in",
        )


class Pet(
    AbstractSimpleNamedModelMixin,
    AbstractTimestampMixin,
    ObjectPermissionModelMixin,
    models.Model,
):
    """
    Holds the information about a single person
    """

    class PetTypeChoices(models.TextChoices):
        CAT = "cat"
        DOG = "dog"
        HORSE = "horse"

    pet_type = models.CharField(  # noqa: DJ001
        max_length=10,
        choices=PetTypeChoices.choices,
        null=True,
        blank=True,
        help_text=_("The type of pet this is"),
    )

    objects: PetQuerySet = PetQuerySet.as_manager()

    def __str__(self) -> str:
        return f"Pet {self.name}"


class PetInImage(AbstractBoxInImage):
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name="pet_appearances",
        help_text=_("Pet is in this Image at the given location"),
        null=True,
    )

    @property
    def name(self) -> str:
        if self.pet:
            return self.pet.name
        return "Unknown"


class ImageSource(AbstractTimestampMixin, AbstractSimpleNamedModelMixin, ObjectPermissionModelMixin, models.Model):
    """ """

    objects: PermittedQueryset = PermittedQueryset.as_manager()

    def __str__(self) -> str:
        return f"Source {self.name}"


class RoughDate(AbstractTimestampMixin, models.Model):
    """
    The rough date of the image
    """

    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
        help_text=_("The year (always required)"),
    )
    month = models.PositiveSmallIntegerField(
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("The month (1-12, null if unknown)"),
    )
    day = models.PositiveSmallIntegerField(
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_("The day (1-31, null if unknown)"),
    )

    # Generated field for comparisons and ordering
    # This creates a date using defaults for missing values
    comparison_date = models.GeneratedField(
        expression=models.expressions.RawSQL(
            "date(printf('%04d-%02d-%02d', year, COALESCE(month, 1), COALESCE(day, 1)))",
            [],
        ),
        output_field=models.DateField(),
        db_persist=True,
    )

    class Meta:
        ordering: Sequence = ["comparison_date"]
        constraints: Sequence = [
            # Logical constraint: day can't exist without month
            models.CheckConstraint(
                condition=models.Q(day__isnull=True) | models.Q(month__isnull=False),
                name="day_requires_month",
            ),
            # Database-level validation for ranges (backup to validators)
            models.CheckConstraint(
                condition=models.Q(year__gte=1, year__lte=9999),
                name="valid_year_range",
            ),
            models.CheckConstraint(
                condition=models.Q(month__isnull=True) | models.Q(month__gte=1, month__lte=12),
                name="valid_month_range",
            ),
            models.CheckConstraint(
                condition=models.Q(day__isnull=True) | models.Q(day__gte=1, day__lte=31),
                name="valid_day_range",
            ),
            # Uniqueness constraints using the separate fields
            # Year-only entries (month and day are null)
            models.UniqueConstraint(
                fields=["year"],
                condition=models.Q(month__isnull=True, day__isnull=True),
                name="unique_year_only",
            ),
            # Year-month entries (day is null, month is not null)
            models.UniqueConstraint(
                fields=["year", "month"],
                condition=models.Q(month__isnull=False, day__isnull=True),
                name="unique_year_month",
            ),
            # Full date entries (all fields present)
            models.UniqueConstraint(
                fields=["year", "month", "day"],
                condition=models.Q(month__isnull=False, day__isnull=False),
                name="unique_full_date",
            ),
        ]

    def __str__(self) -> str:
        if self.day is not None:
            return f"{self.year}-{self.month:02d}-{self.day:02d}"
        if self.month is not None:
            return f"{self.year}-{self.month:02d}-DD"
        return f"{self.year}-MM-DD"

    def __repr__(self) -> str:
        return f"RoughDate: {self!s}"

    @property
    def precision(self):
        """Return the precision level of this date"""
        if self.day is not None:
            return "day"
        if self.month is not None:
            return "month"
        return "year"


class RoughLocation(AbstractTimestampMixin, models.Model):
    """
    Holds the information about a Location where an image was.

    As much information should be filled in as possible, at least the country is required
    """

    country_code = models.CharField(
        max_length=4,
        db_index=True,
        help_text=_("Country code in ISO 3166-1 alpha 2 format"),
    )
    subdivision_code = models.CharField(  # noqa: DJ001
        max_length=12,  # Longest subdivision in the world is 6 characters, double that
        db_index=True,
        null=True,
        help_text=_("State, province or subdivision ISO 3166-2 alpha 2 format"),
    )
    city = models.CharField(  # noqa: DJ001
        max_length=255,
        db_index=True,
        null=True,
        help_text=_("City or town"),
    )
    sub_location = models.CharField(  # noqa: DJ001
        max_length=255,
        db_index=True,
        null=True,
        help_text=_("Detailed location within a city or town"),
    )

    class Meta:
        ordering: Sequence = [
            "country_code",
            "subdivision_code",
            "city",
            "sub_location",
        ]
        constraints: Sequence = [
            # 1. All four fields provided (sub_location NOT NULL)
            models.UniqueConstraint(
                fields=["country_code", "subdivision_code", "city", "sub_location"],
                name="unique_location_all_fields",
                condition=Q(sub_location__isnull=False),
            ),
            # 2. sub_location is NULL, but city is NOT NULL
            models.UniqueConstraint(
                fields=["country_code", "subdivision_code", "city"],
                name="unique_location_no_sub_location",
                condition=Q(sub_location__isnull=True, city__isnull=False),
            ),
            # 3. sub_location and city are NULL, but subdivision_code is NOT NULL
            models.UniqueConstraint(
                fields=["country_code", "subdivision_code"],
                name="unique_location_no_city_sub_location",
                condition=Q(sub_location__isnull=True, city__isnull=True, subdivision_code__isnull=False),
            ),
            # 4. sub_location, city, and subdivision_code are NULL (only country_code provided)
            models.UniqueConstraint(
                fields=["country_code"],
                name="unique_location_only_country",
                condition=Q(sub_location__isnull=True, city__isnull=True, subdivision_code__isnull=True),
            ),
        ]

    def __str__(self) -> str:
        country = Country.from_alpha2(self.country_code)  # type: ignore[arg-type]
        if TYPE_CHECKING:
            assert isinstance(country, Country)
        value = f"Country: {country.best_name} ({country.alpha2})"
        if self.subdivision_code:
            subdivision_name = country.get_subdivision_name(self.subdivision_code)  # type: ignore[arg-type]
            if TYPE_CHECKING:
                assert isinstance(subdivision_name, str)
            value = f"{value} - State: {subdivision_name} ({self.subdivision_code})"
        if self.city:
            value = f"{value} - City: {self.city}"
        if self.sub_location:
            value = f"{value} - Location: {self.sub_location}"
        return value

    def __repr__(self) -> str:
        return f"RoughLocation: {self!s}"

    @property
    def country_name(self) -> str:
        country = Country.from_alpha2(self.country_code)  # type: ignore[arg-type]
        if TYPE_CHECKING:
            # The code is validated
            assert country is not None

        return country.best_name

    @property
    def subdivision_name(self) -> str | None:
        if not self.subdivision_code:
            return None
        country = Country.from_alpha2(self.country_code)  # type: ignore[arg-type]
        if TYPE_CHECKING:
            # The code is validated
            assert country is not None
        return country.get_subdivision_name(self.subdivision_code)  # type: ignore[arg-type]

    @property
    def full_location_display(self) -> str:
        """
        Returns a user-friendly string representation of the location,
        including only the parts that are present.
        """
        parts: list[str] = [self.country_name]
        if self.subdivision_code:
            parts.append(self.subdivision_name)
        if self.city:
            parts.append(self.city)
        if self.sub_location:
            parts.append(self.sub_location)
        return ", ".join(parts)


class ImageFolder(AbstractTimestampMixin, ObjectPermissionModelMixin, TreeNodeModel):
    # Required TreeNodeModel attributes
    treenode_display_field = "name"

    name = models.CharField(max_length=150, db_index=True)

    description = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        db_index=True,
    )

    objects: PermittedQueryset = PermittedQueryset.as_manager()

    class Meta:
        verbose_name = "Folder"
        verbose_name_plural = "Folders"
        constraints: Sequence = [
            # Constraint 1: For non-root folders (where tn_parent is NOT NULL)
            # Ensures uniqueness of 'name' within a specific parent folder.
            models.UniqueConstraint(
                fields=["tn_parent", "name"],
                name="unique_folder_name_per_parent",
                condition=~Q(tn_parent__isnull=True),
            ),
            # Constraint 2: For root-level folders (where tn_parent IS NULL)
            # Ensures that root folders have unique names.
            models.UniqueConstraint(
                fields=["name"],  # Only 'name' needs to be unique for root folders
                name="unique_root_folder_name",
                condition=Q(tn_parent__isnull=True),
            ),
        ]
