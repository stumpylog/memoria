from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from memoria.models.image import Image  # noqa: F401

from django.db import models
from simpleiso3166 import Country
from treenode.models import TreeNodeModel

from memoria.models.abstract import AbstractBoxInImage
from memoria.models.abstract import AbstractSimpleNamedModelMixin
from memoria.models.abstract import AbstractTimestampMixin
from memoria.models.abstract import ObjectPermissionModelMixin
from memoria.models.abstract import PermittedQueryset


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
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, help_text="Tag is on this Image")

    image = models.ForeignKey(
        "Image",
        on_delete=models.CASCADE,
        help_text="A Tag is on this Image",
    )

    applied = models.BooleanField(default=False, help_text="This tag is applied to this image")


class PersonQuerySet(PermittedQueryset):
    def with_images(self) -> PersonQuerySet:
        """
        Fetches the person with Images
        """
        return self.prefetch_related(
            "images",
        )


class Person(AbstractSimpleNamedModelMixin, AbstractTimestampMixin, ObjectPermissionModelMixin, models.Model):
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
        related_name="images",
        help_text="Person is in this Image at the given location",
    )

    exclude_from_training = models.BooleanField(
        default=False,
        help_text="For future growth, do not use this box for facial recognition training",
    )

    @property
    def name(self) -> str:
        if self.person:
            return self.person.name
        return "Unknown"


class Pet(AbstractSimpleNamedModelMixin, AbstractTimestampMixin, ObjectPermissionModelMixin, models.Model):
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
        help_text="The type of pet this is",
    )

    objects = PermittedQueryset.as_manager()

    def __str__(self) -> str:
        return f"Pet {self.name}"


class PetInImage(AbstractBoxInImage):
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name="images",
        help_text="Pet is in this Image at the given location",
        null=True,
    )

    @property
    def name(self) -> str:
        if self.pet:
            return self.pet.name
        return "Unknown"


class ImageSource(AbstractTimestampMixin, AbstractSimpleNamedModelMixin, ObjectPermissionModelMixin, models.Model):
    """ """

    objects = PermittedQueryset.as_manager()

    def __str__(self) -> str:
        return f"Source {self.name}"


class RoughDate(AbstractTimestampMixin, ObjectPermissionModelMixin, models.Model):
    """
    The rough date of the image
    """

    date = models.DateField(
        unique=True,
        help_text="The date of the image, maybe not exact",
    )

    month_valid = models.BooleanField(
        default=False,
        help_text="Is the month of this date valid?",
    )
    day_valid = models.BooleanField(
        default=False,
        help_text="Is the day of this date valid?",
    )

    objects = PermittedQueryset.as_manager()

    class Meta:
        ordering: Sequence = ["date"]
        constraints: Sequence = [
            models.CheckConstraint(
                condition=(models.Q(day_valid=False) | ~models.Q(month_valid=False)),
                name="invalid-month-day-combo",
            ),
            models.UniqueConstraint(
                fields=["date", "month_valid", "day_valid"],
                name="unique-date",
            ),
        ]

    def __str__(self) -> str:
        year = self.date.year
        month = self.date.month if self.month_valid else "MM"
        day = self.date.day if self.day_valid else "DD"
        return f"{year}-{month}-{day}"

    def __repr__(self) -> str:
        return f"RoughDate: {self!s}"


class RoughLocation(AbstractTimestampMixin, ObjectPermissionModelMixin, models.Model):
    """
    Holds the information about a Location where an image was.

    As much information should be filled in as possible, at least the country is required
    """

    country_code = models.CharField(
        max_length=4,
        db_index=True,
        help_text="Country code in ISO 3166-1 alpha 2 format",
    )
    subdivision_code = models.CharField(  # noqa: DJ001
        max_length=12,  # Longest subdivision in the world is 6 characters, double that
        db_index=True,
        null=True,
        blank=True,
        help_text="State, province or subdivision ISO 3166-2 alpha 2 format",
    )
    city = models.CharField(  # noqa: DJ001
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="City or town",
    )
    sub_location = models.CharField(  # noqa: DJ001
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="Detailed location within a city or Town",
    )

    objects = PermittedQueryset.as_manager()

    class Meta:
        ordering: Sequence = [
            "country_code",
            "subdivision_code",
            "city",
            "sub_location",
        ]
        constraints: Sequence = [
            models.UniqueConstraint(
                fields=["country_code", "subdivision_code", "city", "sub_location"],
                name="unique-location",
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


class ImageFolder(AbstractTimestampMixin, AbstractSimpleNamedModelMixin, ObjectPermissionModelMixin, TreeNodeModel):
    # Required TreeNodeModel attributes
    treenode_display_field = "name"

    objects: PermittedQueryset = PermittedQueryset.as_manager()

    class Meta:
        verbose_name = "Folder"
        verbose_name_plural = "Folders"

    def move_to(self, target_folder: ImageFolder | None = None):
        """
        Move this folder to become a child of the target folder.
        If target_folder is None, this will become a root folder.
        """
        self.set_parent(target_folder)
        self.save()
