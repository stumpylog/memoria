from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


from django.db import models
from django.db.models import Count
from django.db.models import Prefetch

from memoria.models.abstract import AbstractSimpleNamedModelMixin
from memoria.models.abstract import AbstractTimestampMixin
from memoria.models.abstract import ObjectPermissionModelMixin
from memoria.models.abstract import PermittedQueryset
from memoria.models.image import Image


class AlbumQueryset(PermittedQueryset):  # type: ignore[valid-type] # Ignore if PermittedQueryset is not typed
    """
    Custom queryset for the Album model with useful methods.
    """

    def with_images(self) -> AlbumQueryset:
        """
        Prefetches all images for each album using the default ManyToMany manager.
        Does NOT guarantee the custom sort order. Use .with_ordered_images() for that.
        Access the prefetched images via album.images.all() (or similar manager methods).
        """
        return self.prefetch_related("images")

    def with_ordered_images(self) -> AlbumQueryset:
        """
        Prefetches images for each album, ordered by ImageInAlbum.sort_order.
        Stores the prefetched, ordered images in a custom attribute
        'prefetched_ordered_images' on each Album instance.
        Access them like `album.prefetched_ordered_images`.
        """

        return self.prefetch_related(
            Prefetch(
                "images",
                queryset=Image.objects.order_by("imageinalbum__sort_order"),
                to_attr="prefetched_ordered_images",
            ),
        )

    def with_image_count(self) -> AlbumQueryset:
        """
        Annotates each album with the number of related images.
        Access the count via the '_image_count' attribute on each album instance.
        """
        # Use the name of the ManyToMany relation ('images') to count
        return self.annotate(image_count=Count("images"))


class Album(AbstractSimpleNamedModelMixin, AbstractTimestampMixin, ObjectPermissionModelMixin, models.Model):
    """
    Holds multiple Images in an ordered form, with a name and optional description
    """

    images = models.ManyToManyField(
        "Image",
        through="ImageInAlbum",
        related_name="albums",
    )

    objects: AlbumQueryset = AlbumQueryset.as_manager()

    def __str__(self) -> str:
        return f"Album: {self.name}"

    def image_ids(self) -> list[int]:
        """
        The sorted list of image IDs in this album
        """
        return list(
            self.images.order_by("imageinalbum__sort_order").values_list(
                "id",
                flat=True,
            ),
        )

    def view_group_ids(self):
        return [g.id for g in self.view_groups.all()]

    @property
    def edit_group_ids(self):
        return [g.id for g in self.edit_groups.all()]

    def get_ordered_images(self) -> models.QuerySet[Image]:
        """
        Returns the images related to this album in the specified sort order.
        This hits the database per album unless prefetched correctly.
        Consider using with_ordered_images() on a queryset for multiple albums.
        """
        return self.images.order_by("imageinalbum__sort_order")


class ImageInAlbum(AbstractTimestampMixin, models.Model):
    """
    Through model to hold the ordering for single image in an album
    """

    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
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
