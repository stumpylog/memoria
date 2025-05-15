from typing import Final

from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from memoria.models.abstract import AbstractTimestampMixin

DEFAULT_SINGLETON_INSTANCE_ID: Final[int] = 1


class SiteSettings(AbstractTimestampMixin, models.Model):
    """
    Settings which are common across more than 1 parser
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
        validators=[MinValueValidator(1), MaxValueValidator(800)],
        default=500,
    )

    class Meta:
        verbose_name = _("memoria site-wide application settings")

    def __str__(self) -> str:  # pragma: no cover
        return "SiteAdminSettings"

    def save(self, *args, **kwargs):
        """
        Always save as the first and only model
        """
        self.pk = DEFAULT_SINGLETON_INSTANCE_ID
        super().save(*args, **kwargs)
