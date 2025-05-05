from collections.abc import Sequence
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models

if TYPE_CHECKING:
    from memoria.models.image import Image  # noqa: F401

TUser = get_user_model()


class AbstractTimestampMixin(models.Model):
    """
    Mixin class to provide created_at and updated_at columns in UTC
    """

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AbstractSimpleNamedModelMixin(models.Model):
    """
    Basic model which provides a short name column and longer description column
    """

    name = models.CharField(max_length=100, unique=True, db_index=True)

    description = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class AbstractBoxInImage(AbstractTimestampMixin, models.Model):
    """
    Holds information for a bounding box in an image, ideally tied to a Person or Per
    """

    image = models.ForeignKey(
        "Image",
        on_delete=models.CASCADE,
        help_text="A Thing is in this Image at the given location",
    )

    # bounding box around a region
    # These are stored as relative values, with 1.0 being the most
    center_x = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    center_y = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    height = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    width = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    description = models.CharField(  # noqa: DJ001
        verbose_name="Optional description of the region",
        max_length=2048,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class AccessModelMixin(models.Model):
    view_groups: models.ManyToManyField = models.ManyToManyField(
        Group,
        related_name="%(class)s_viewers",
    )
    edit_groups: models.ManyToManyField = models.ManyToManyField(
        Group,
        related_name="%(class)s_editors",
    )

    # TODO: Investigate using GeneratedField for the sounds

    class Meta:
        abstract = True
        indexes: Sequence = [models.Index(fields=["view_group_count", "edit_group_count"])]

    def is_viewable_by(self, user: TUser) -> bool:
        if not user.is_active:
            return False
        if user.is_superuser:
            return True
        if self.view_groups.count() == 0 and self.edit_groups.count() == 0:
            return True
        groups = user.groups.all()
        return self.view_groups.filter(id__in=groups).exists() or self.edit_groups.filter(id__in=groups).exists()

    def is_editable_by(self, user: TUser) -> bool:
        if not user.is_active:
            return False
        if user.is_superuser:
            return True
        return self.edit_groups.filter(id__in=user.groups.all()).exists()
