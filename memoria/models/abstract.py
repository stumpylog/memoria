from typing import TYPE_CHECKING
from typing import Self

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.db.models import FloatField
from django.db.models import GeneratedField
from django.db.models import Q
from django.db.models.query import QuerySet

if TYPE_CHECKING:
    from memoria.models.image import Image  # noqa: F401


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

    # Generated fields for CSS properties (calculated in the database)
    # The values are stored as percentages (0 to 100)
    top_percent_value = GeneratedField(
        expression=(F("center_y") - F("height") / 2) * 100,
        output_field=FloatField(),
        db_persist=True,
        verbose_name="Top position in percent",
    )

    left_percent_value = GeneratedField(
        expression=(F("center_x") - F("width") / 2) * 100,
        output_field=FloatField(),
        db_persist=True,
        verbose_name="Left position in percent",
    )

    width_percent_value = GeneratedField(
        expression=F("width") * 100,
        output_field=FloatField(),
        db_persist=True,
        verbose_name="Width in percent",
    )

    height_percent_value = GeneratedField(
        expression=F("height") * 100,
        output_field=FloatField(),
        db_persist=True,
        verbose_name="Height in percent",
    )

    class Meta:
        abstract = True

    # Python properties for easy access with the '%' sign for CSS
    @property
    def top_css(self) -> str:
        """Returns the top position as a CSS percentage string."""
        # Using the generated field value
        return f"{self.top_percent_value:.2f}%"  # Format to 2 decimal places

    @property
    def left_css(self) -> str:
        """Returns the left position as a CSS percentage string."""
        # Using the generated field value
        return f"{self.left_percent_value:.2f}%"  # Format to 2 decimal places

    @property
    def width_css(self) -> str:
        """Returns the width as a CSS percentage string."""
        # Using the generated field value
        return f"{self.width_percent_value:.2f}%"  # Format to 2 decimal places

    @property
    def height_css(self) -> str:
        """Returns the height as a CSS percentage string."""
        # Using the generated field value
        return f"{self.height_percent_value:.2f}%"  # Format to 2 decimal places

    @property
    def bounding_box_style(self) -> str:
        """Returns a full CSS style string for the bounding box."""
        return f"top: {self.top_css}; left: {self.left_css}; width: {self.width_css}; height: {self.height_css};"


class ObjectPermissionModelMixin(models.Model):
    """
    Abstract model providing view/edit group relations.
    """

    view_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="%(class)ss_viewable",
        help_text="Groups allowed to view this object",
    )
    edit_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="%(class)ss_editable",
        help_text="Groups allowed to edit this object",
    )

    class Meta:
        abstract = True


class PermittedQueryset(QuerySet):
    def permitted(self, user: User) -> Self:
        """
        Filters objects to only include those the user has permission to view or edit.
        """
        if user.is_superuser:
            return self  # Superusers can see everything

        if not user.groups.exists():
            # User has no groups, so they can't view anything via group permissions
            return self.none()  # Return an empty queryset

        # Filter objects where *any* of the user's group IDs are in the image's view_groups OR edit_groups
        # Use Q objects for OR logic and __in lookup for efficiency
        return self.filter(
            Q(view_groups__in=user.groups.all()) | Q(edit_groups__in=user.groups.all()),
        ).distinct()  # Use distinct in case an image is in multiple relevant groups

    @classmethod
    def get_permitted_filter_q(cls, user: User) -> Q | None:
        """
        Returns the Q object representing the 'permitted' filter for a user.
        This can be used in annotations or other filtering operations.
        Returns None for superusers (indicating no filter needed).
        Returns Q(pk__in=[]) for users with no groups (indicating no objects match).

        Note: This method assumes the model fields 'view_groups' and 'edit_groups'
        exist on the model this QuerySet is used for (e.g., your Image model).
        """
        if user.is_superuser:
            # No specific filter is needed for superusers; they see everything.
            # Returning None signals that no filter should be applied in Count.
            return Q()
        if not user.groups.exists():
            # If the user has no groups, the group-based filter will match nothing.
            # We represent this with a Q object that guarantees no match.
            # Assuming the model has a primary key named 'pk'.
            return Q(pk__in=[])
        # Construct the Q object based on user's group memberships.
        # The field names 'view_groups' and 'edit_groups' refer to fields
        # on the model this QuerySet is applied to (e.g., Image model).
        user_groups = user.groups.all()
        return Q(view_groups__in=user_groups) | Q(edit_groups__in=user_groups)
