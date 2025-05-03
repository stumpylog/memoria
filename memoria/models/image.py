from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from blake3 import blake3
from django.conf import settings
from django.db import models
from exifmwg.models import RotationEnum
from imagehash import average_hash
from PIL import Image as PILImage

from memoria.models.abstract import AbstractTimestampMixin
from memoria.models.metadata import ImageSource
from memoria.models.metadata import Person
from memoria.models.metadata import PersonInImage
from memoria.models.metadata import Pet
from memoria.models.metadata import PetInImage
from memoria.models.metadata import RoughDate
from memoria.models.metadata import RoughLocation
from memoria.models.metadata import Tag
from memoria.models.metadata import TagOnImage
from memoria.models.permissions import PermissionManager
from memoria.models.permissions import PermissionMixin

if TYPE_CHECKING:
    from collections.abc import Sequence


class Image(AbstractTimestampMixin, PermissionMixin, models.Model):
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

    # TODO: These two might not be needed, as the production server probably handles the etag/last modified
    thumbnail_checksum = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="blake3 hex digest",
        help_text="The BLAKE3 checksum of the image thumbnail",
    )

    full_size_checksum = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="blake3 hex digest",
        help_text="The BLAKE3 checksum of the full size image",
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

    height = models.PositiveIntegerField(verbose_name="height in pixels")
    width = models.PositiveIntegerField(verbose_name="width in pixels")

    orientation = models.PositiveSmallIntegerField(
        choices=OrientationChoices.choices,
        default=OrientationChoices.HORIZONTAL,
        help_text="MWG Orientation flag",
    )

    description = models.TextField(  # noqa: DJ001
        null=True,
        blank=True,
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

    permissions_manager = PermissionManager()

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

    def update_hashes(self, *, threads=4) -> None:
        def hash_file(filepath: Path, *, hash_threads: int = 4) -> str:
            return blake3(
                filepath.read_bytes(),
                max_threads=hash_threads,
            ).hexdigest()

        with PILImage.open(self.original_path) as im_file:
            self.phash = str(average_hash(im_file))

        self.original_checksum = hash_file(self.original_path, hash_threads=threads)
        self.full_size_checksum = hash_file(self.full_size_path, hash_threads=threads)
        self.thumbnail_checksum = hash_file(self.thumbnail_path, hash_threads=threads)

        self.save()
