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
    """
    A queryset mixin providing methods to filter objects based on user permissions
    defined by 'view_groups' and 'edit_groups' ManyToManyField fields on a model.
    """

    @classmethod
    def _get_base_permission_q_for_groups(cls, user_groups: QuerySet[Group], group_field_name: str) -> Q:
        """
        Helper method to generate the base Q object for a given permission type
        based on a pre-fetched set of user groups.
        """
        return Q(**{f"{group_field_name}__in": user_groups})

    @classmethod
    def get_viewable_filter_q(cls, user: User) -> Q:
        """
        Returns a Q object for filtering objects viewable by the user.
        An object is viewable if the user is in its 'view_groups' OR 'edit_groups'.
        """
        if not user.is_authenticated:
            return Q(pk__in=[])  # Matches nothing for unauthenticated users

        if user.is_superuser:
            return Q()  # Superuser can view anything

        user_groups = user.groups.all()
        if not user_groups.exists():
            # User has no groups, so they can't view anything via group permissions
            return Q(pk__in=[])  # Matches nothing

        view_q = cls._get_base_permission_q_for_groups(user_groups, "view_groups")
        edit_q_for_view = cls._get_base_permission_q_for_groups(user_groups, "edit_groups")

        # Users can view if they are in view_groups OR if they are in edit_groups
        return view_q | edit_q_for_view

    @classmethod
    def get_editable_filter_q(cls, user: User) -> Q:
        """
        Returns a Q object for filtering objects editable by the user.
        An object is editable ONLY if the user is in its 'edit_groups'.
        """
        if not user.is_authenticated:
            return Q(pk__in=[])

        if user.is_superuser:
            return Q()  # Superuser can edit anything

        user_groups = user.groups.all()
        if not user_groups.exists():
            # User has no groups, so they can't edit anything via group permissions
            return Q(pk__in=[])

        return cls._get_base_permission_q_for_groups(user_groups, "edit_groups")

    @classmethod
    def get_permitted_filter_q(cls, user: User) -> Q:
        """
        Returns the Q object representing the general 'permitted to access' filter
        (i.e., view access) for a user.
        An object is permitted if the user can view it (either via view_groups or edit_groups).
        """
        # "Permitted to access" means "can view".
        # get_viewable_filter_q already correctly combines view_groups and edit_groups for visibility.
        return cls.get_viewable_filter_q(user)

    def viewable_by(self, user: User) -> Self:
        """
        Filters the queryset to objects viewable by the given user.
        (User is in view_groups OR edit_groups)
        """
        return self.filter(self.get_viewable_filter_q(user)).distinct()

    def editable_by(self, user: User) -> Self:
        """
        Filters the queryset to objects editable by the given user.
        (User is in edit_groups)
        """
        return self.filter(self.get_editable_filter_q(user)).distinct()

    def permitted(self, user: User) -> Self:
        """
        Filters objects to only include those the user has general permission to access (view).
        This relies on viewable_by, which correctly checks if user is in view_groups OR edit_groups.
        """
        return self.viewable_by(user)
