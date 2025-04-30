from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from memoria.models.image import Image  # noqa: F401


from django.db import models

from memoria.models.abstract import AbstractSimpleNamedModel
from memoria.models.abstract import AbstractTimestampMixin


class Album(AbstractSimpleNamedModel, AbstractTimestampMixin, models.Model):
    """
    Holds multiple Images in an ordered form, with a name and optional description
    """

    images = models.ManyToManyField(
        "Image",
        through="ImageInAlbum",
        related_name="albums",
    )

    def __str__(self) -> str:
        return f"Album: {self.name}"

    def image_ids(self) -> list[int]:
        return list(
            self.images.order_by("imageinalbum__sort_order").values_list(
                "id",
                flat=True,
            ),
        )


class ImageInAlbum(AbstractTimestampMixin, models.Model):
    """
    Through model to hold the ordering for single image in an album
    """

    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        null=True,
    )
    image = models.ForeignKey(
        "Image",
        on_delete=models.CASCADE,
    )

    sort_order = models.PositiveBigIntegerField(
        verbose_name="Order of this image in the album",
    )

    class Meta:
        ordering: Sequence = ["sort_order"]
        constraints: Sequence = [
            models.UniqueConstraint(
                fields=["sort_order", "album"],
                name="sorting-to-album",
            ),
        ]

    def __str__(self) -> str:
        return f"Image {self.image} in album {self.album}"
