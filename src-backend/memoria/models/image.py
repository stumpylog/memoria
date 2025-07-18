from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from memoria.models.abstract import AbstractTimestampMixin
from memoria.models.abstract import ObjectPermissionModelMixin
from memoria.models.abstract import PermittedQueryset
from memoria.models.metadata import ImageFolder
from memoria.models.metadata import ImageSource
from memoria.models.metadata import Person
from memoria.models.metadata import PersonInImage
from memoria.models.metadata import Pet
from memoria.models.metadata import PetInImage
from memoria.models.metadata import RoughDate
from memoria.models.metadata import RoughLocation
from memoria.models.metadata import Tag
from memoria.models.metadata import TagOnImage

UserModelT = get_user_model()

if TYPE_CHECKING:
    from collections.abc import Sequence


class ImageQuerySet(PermittedQueryset):
    def with_location(self) -> ImageQuerySet:
        return self.select_related("location")

    def with_folder(self) -> ImageQuerySet:
        return self.select_related("folder")

    def with_date(self) -> ImageQuerySet:
        return self.select_related("date")

    def with_tags(self) -> ImageQuerySet:
        return self.prefetch_related("tags")

    def with_people(self) -> ImageQuerySet:
        """
        Fetches Image with related people
        """
        return self.prefetch_related(
            "people",
        )

    def with_people_and_boxes(self) -> ImageQuerySet:
        return self.prefetch_related(
            models.Prefetch(
                "personinimage_set",
                queryset=PersonInImage.objects.select_related("person"),
            ),
        )

    def with_pets(self) -> ImageQuerySet:
        """
        Fetches Image with related pets
        """
        return self.prefetch_related(
            "pets",
            "petinimage_set__pet",
        )

    def with_pets_and_boxes(self) -> ImageQuerySet:
        return self.prefetch_related(
            models.Prefetch(
                "petinimage_set",
                queryset=PetInImage.objects.select_related("pet"),
            ),
        )


class Image(AbstractTimestampMixin, ObjectPermissionModelMixin, models.Model):
    """
    Holds the information about an Image.  Basically everything relates to an image somehow
    """

    class OrientationChoices(models.IntegerChoices):
        HORIZONTAL = 1, _("Horizontal")
        MIRROR_HORIZONTAL = 2, _("Mirror Horizontal")
        ROTATE_180 = 3, _("Rotate 180")
        MIRROR_VERTICAL = 4, _("Mirror Vertical")
        MIRROR_HORIZONTAL_AND_ROTATE_270_CW = 5, _("Mirror Horizontal And Rotate 270 Cw")
        ROTATE_90_CW = 6, _("Rotate 90 Cw")
        MIRROR_HORIZONTAL_AND_ROTATE_90_CW = 7, _("Mirror Horizontal And Rotate 90 Cw")
        ROTATE_270_CW = 8, _("Rotate 270 Cw")

    original_checksum = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="blake3 hex digest",
        help_text=_("The BLAKE3 checksum of the original file"),
    )

    phash = models.CharField(
        max_length=32,
        db_index=True,
        verbose_name="perceptual average hash of the image",
        help_text=_("The pHash (average) of the original file"),
    )

    file_size = models.PositiveBigIntegerField(
        verbose_name="file size in bytes",
        help_text=_("Size of the original file in bytes"),
    )

    original_height = models.PositiveIntegerField(verbose_name="original image height in pixels")
    original_width = models.PositiveIntegerField(verbose_name="original image width in pixels")

    large_version_height = models.PositiveSmallIntegerField(verbose_name="Large size image height in pixels")
    large_version_width = models.PositiveSmallIntegerField(verbose_name="Large size image width in pixels")

    thumbnail_height = models.PositiveSmallIntegerField(verbose_name="Thumbnail image height in pixels")
    thumbnail_width = models.PositiveSmallIntegerField(verbose_name="Thumbnail image width in pixels")

    orientation = models.PositiveSmallIntegerField(
        choices=OrientationChoices.choices,
        default=OrientationChoices.HORIZONTAL,
        help_text=_("MWG Orientation flag"),
    )

    title = models.TextField(
        help_text=_("Title of the image (used for display only currently)"),
    )

    description = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        help_text=_("MWG Description tag"),
    )

    original = models.CharField(
        max_length=4096,
        unique=True,
        verbose_name="Path to the original image",
    )

    is_dirty = models.BooleanField(
        default=False,
        help_text=_("The metadata is dirty and needs to be synced to the file"),
    )

    deleted_at = models.DateTimeField(
        default=None,
        null=True,
        help_text=_("Date the image was deleted or None if it has not been"),
    )

    is_starred = models.BooleanField(
        default=False,
        help_text=_("The image has been starred"),
    )

    source = models.ForeignKey(
        ImageSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
        help_text=_("Source of the original image (box, deck, carousel, etc)"),
    )

    location = models.ForeignKey(
        RoughLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
        help_text=_("Location where the image was taken, with as much refinement as possible"),
    )

    date = models.ForeignKey(
        RoughDate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
        help_text=_("RoughDate when the image was taken, with as much refinement as possible"),
    )

    people = models.ManyToManyField(
        Person,
        through=PersonInImage,
        help_text=_("These people are in the image"),
        related_name="images_featured_in",
    )

    pets = models.ManyToManyField(
        Pet,
        through=PetInImage,
        help_text=_("These pets are in the image"),
        related_name="images_featured_in",
    )

    tags = models.ManyToManyField(
        Tag,
        through=TagOnImage,
        help_text=_("These tags apply to the image"),
    )

    folder = models.ForeignKey(
        ImageFolder,
        related_name="images",
        on_delete=models.CASCADE,
        help_text=_("The folder this image belongs to"),
    )

    objects: ImageQuerySet = ImageQuerySet.as_manager()

    class Meta:
        ordering: Sequence[str] = ["pk"]

    def __str__(self) -> str:
        return f"Image {self.original_path.name}"

    @property
    def original_path(self) -> Path:
        return Path(self.original).resolve()

    @original_path.setter
    def original_path(self, value: Path) -> None:
        self.original = str(value.resolve())

    @property
    def thumbnail_path(self) -> Path:
        if TYPE_CHECKING:
            assert hasattr(settings, "THUMBNAIL_DIR")
            assert isinstance(settings.THUMBNAIL_DIR, Path)
        return (settings.THUMBNAIL_DIR / self.image_fs_id).with_suffix(".webp").resolve()

    @property
    def thumbnail_url(self) -> str | None:
        """
        Constructs the full URL for the thumbnail.
        """
        return settings.MEDIA_URL + self.thumbnail_path.relative_to(settings.MEDIA_ROOT).as_posix()

    @property
    def full_size_path(self) -> Path:
        if TYPE_CHECKING:
            assert isinstance(settings.LARGE_SIZE_DIR, Path)
        return (settings.LARGE_SIZE_DIR / self.image_fs_id).with_suffix(".webp").resolve()

    @property
    def larger_size_url(self) -> str | None:
        """
        Constructs the full URL for the full size image.
        """
        return settings.MEDIA_URL + self.full_size_path.relative_to(settings.MEDIA_ROOT).as_posix()

    @property
    def image_fs_id(self) -> str:
        return f"{self.pk:010}"

    def mark_as_clean(self) -> None:
        """
        Helper to mark an image as clean
        """
        Image.objects.filter(pk=self.pk).update(is_dirty=False)
