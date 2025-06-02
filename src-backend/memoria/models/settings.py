from collections.abc import Sequence
from typing import Final

from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from memoria.models.abstract import AbstractTimestampMixin

DEFAULT_SINGLETON_INSTANCE_ID: Final[int] = 1


class SiteSettings(AbstractTimestampMixin, models.Model):
    """
    Settings which are common across the entire site.

    Configured by staff or superusers only.
    """

    class ImageScaledSideMaxChoices(models.IntegerChoices):
        """
        Choices for the maximum side length of a scaled image.
        These values are commonly used for responsive image breakpoints.
        """

        SMALL = 768, _("768px (Tablet/Small Screen)")
        MEDIUM = 1024, _("1024px (Tablet Landscape/Laptop)")
        LARGE = 1920, _("1920px (HD/Desktop)")
        XLARGE = 2560, _("2560px (QHD/Large Desktop)")
        XXLARGE = 3840, _("3840px (4K/HiDPI Desktop)")
        # XXXLARGE = 4500, _("4500px (Very Large)")
        # QUADHD = 5120, _("5120px (5K/2x QHD)")

    class ThumbnailSizeChoices(models.IntegerChoices):
        """
        Defines standard pixel dimensions for image thumbnails.
        The value represents the maximum dimension (width or height)
        of the thumbnail, with aspect ratio preserved.
        """

        TINY = 128, _("128px (Tiny)")
        SMALL = 256, _("256px (Small)")
        MEDIUM = 512, _("512px (Medium)")
        LARGE = 640, _("640px (Large)")
        XLARGE = 800, _("800px (X-Large)")

    class HashThreadCountChoices(models.IntegerChoices):
        AUTO = -1, _("Auto (blake3.AUTO)")
        SINGLE = 1, _("Single Thread")
        DUAL = 2, _("Dual Thread")
        QUAD = 4, _("Quad Thread")
        OCTA = 8, _("Octa Thread")
        HEXA = 16, _("16 Threads")

    class BatchSizeChoices(models.IntegerChoices):
        """
        Represents a batch size for tasks, from 10 to 100 in increments of 10.
        """

        TEN = 10, "10"
        TWENTY = 20, "20"
        THIRTY = 30, "30"
        FORTY = 40, "40"
        FIFTY = 50, "50"
        SIXTY = 60, "60"
        SEVENTY = 70, "70"
        EIGHTY = 80, "80"
        NINETY = 90, "90"
        ONE_HUNDRED = 100, "100"

    large_image_max_size = models.PositiveSmallIntegerField(
        verbose_name=_("The largest side dimension of generated large images"),
        choices=ImageScaledSideMaxChoices.choices,
        default=ImageScaledSideMaxChoices.XLARGE,
    )

    large_image_quality = models.PositiveSmallIntegerField(
        verbose_name=_("The WebP quality setting for generate large images"),
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        default=90,
    )

    thumbnail_max_size = models.PositiveSmallIntegerField(
        verbose_name=_("The largest side dimension of generated image thumbnails"),
        choices=ThumbnailSizeChoices.choices,
        default=ThumbnailSizeChoices.MEDIUM,
    )

    hash_threads = models.SmallIntegerField(
        verbose_name=_("The number of threads to use when calculating blake3 hashes"),
        choices=HashThreadCountChoices.choices,
        default=HashThreadCountChoices.QUAD,
    )

    batch_size = models.PositiveSmallIntegerField(
        verbose_name=_("For indexing and syncing tasks, the default number of images per task"),
        choices=BatchSizeChoices.choices,
        default=BatchSizeChoices.TEN,
    )

    root_dir = models.CharField(  # noqa: DJ001
        max_length=4096,
        unique=True,
        null=True,
        verbose_name=_("Root directory where image folders are found"),
    )

    class Meta:
        verbose_name = _("memoria site-wide application settings")
        constraints: Sequence = [
            # Additional enforcement of validators
            models.CheckConstraint(
                condition=models.Q(large_image_quality__gte=1, large_image_quality__lte=100),
                name="webp_quality_limit_check",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return "SiteAdminSettings"

    def save(self, *args, **kwargs):
        """
        Always save as the first and only model
        """
        self.pk = DEFAULT_SINGLETON_INSTANCE_ID
        super().save(*args, **kwargs)
