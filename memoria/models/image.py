from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from exifmwg.models import RotationEnum

from memoria.models.abstract import AbstractTimestampMixin
from memoria.models.abstract import ObjectPermissionModelMixin
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

if TYPE_CHECKING:
    from collections.abc import Sequence


class Image(AbstractTimestampMixin, ObjectPermissionModelMixin, models.Model):
    """
    Holds the information about an Image.  Basically everything relates to an image somehow
    """

    class OrientationChoices(models.IntegerChoices):
        HORIZONTAL = RotationEnum.HORIZONTAL.value
        MIRROR_HORIZONTAL = RotationEnum.MIRROR_HORIZONTAL.value
        ROTATE_180 = RotationEnum.ROTATE_180.value
        MIRROR_VERTICAL = RotationEnum.MIRROR_VERTICAL.value
        MIRROR_HORIZONTAL_AND_ROTATE_270_CW = RotationEnum.MIRROR_HORIZONTAL_AND_ROTATE_270_CW.value
        ROTATE_90_CW = RotationEnum.ROTATE_90_CW.value
        MIRROR_HORIZONTAL_AND_ROTATE_90_CW = RotationEnum.MIRROR_HORIZONTAL_AND_ROTATE_90_CW.value
        ROTATE_270_CW = RotationEnum.ROTATE_270_CW.value

    original_checksum = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="blake3 hex digest",
        help_text="The BLAKE3 checksum of the original file",
    )

    phash = models.CharField(
        max_length=32,
        db_index=True,
        verbose_name="perceptual average hash of the image",
        help_text="The pHash (average) of the original file",
    )

    file_size = models.PositiveBigIntegerField(
        verbose_name="file size in bytes",
        help_text="Size of the original file in bytes",
    )

    original_height = models.PositiveIntegerField(verbose_name="original image height in pixels")
    original_width = models.PositiveIntegerField(verbose_name="original image width in pixels")

    thumbnail_height = models.PositiveSmallIntegerField(verbose_name="Thumbnail image height in pixels")
    thumbnail_width = models.PositiveSmallIntegerField(verbose_name="Thumbnail image width in pixels")

    orientation = models.PositiveSmallIntegerField(
        choices=OrientationChoices.choices,
        default=OrientationChoices.HORIZONTAL,
        help_text="MWG Orientation flag",
    )

    title = models.TextField(
        help_text="Title of the image (used for display only currently)",
    )

    description = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        help_text="MWG Description tag",
    )

    original = models.CharField(
        max_length=1024,
        unique=True,
        verbose_name="Path to the original image",
    )

    is_dirty = models.BooleanField(
        default=False,
        help_text="The metadata is dirty and needs to be synced to the file",
    )

    deleted_at = models.DateTimeField(
        default=None,
        null=True,
        help_text="Date the image was deleted or None if it has not been",
    )

    is_starred = models.BooleanField(
        default=False,
        help_text="The image has been starred",
    )

    source = models.ForeignKey(
        ImageSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
        help_text="Source of the original image (box, deck, carousel, etc)",
    )

    location = models.ForeignKey(
        RoughLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
        help_text="Location where the image was taken, with as much refinement as possible",
    )

    date = models.ForeignKey(
        RoughDate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
        help_text="RoughDate when the image was taken, with as much refinement as possible",
    )

    people = models.ManyToManyField(
        Person,
        through=PersonInImage,
        help_text="These people are in the image",
    )

    pets = models.ManyToManyField(
        Pet,
        through=PetInImage,
        help_text="These pets are in the image",
    )

    tags = models.ManyToManyField(
        Tag,
        through=TagOnImage,
        help_text="These tags apply to the image",
    )

    folder = models.ForeignKey(
        ImageFolder,
        related_name="images",
        on_delete=models.CASCADE,
        help_text="The folder this image belongs to",
    )

    class Meta:
        ordering: Sequence[str] = ["pk"]

    def __str__(self) -> str:
        return f"Image {self.original_path.name}"

    @property
    def original_path(self) -> Path:
        return Path(self.original).resolve()

    @original_path.setter
    def original_path(self, path: Path | str) -> None:
        self.original = str(Path(path).resolve())

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
            assert isinstance(settings.FULL_SIZE_DIR, Path)
        return (settings.FULL_SIZE_DIR / self.image_fs_id).with_suffix(".webp").resolve()

    @property
    def full_size_url(self) -> str | None:
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
