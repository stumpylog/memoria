from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Q


class ObjectPermission(models.Model):
    """
    Defines view/edit permissions for any model instance
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # Who has permission
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)

    # Type of permission
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | models.Q(group__isnull=False),
                name="permission_has_user_or_group",
            ),
            # Must have at least one permission
            models.CheckConstraint(
                condition=models.Q(can_view=True) | models.Q(can_edit=True),
                name="permission_has_permission_flag",
            ),
        ]
        indexes = [  # noqa: RUF012
            models.Index(
                fields=["content_type", "object_id"],
                name="objectperm_ct_obj_idx",
            ),
            models.Index(
                fields=["content_type", "object_id", "user"],
                name="objectperm_ct_obj_user_idx",
            ),
            models.Index(
                fields=["content_type", "object_id", "group"],
                name="objectperm_ct_obj_group_idx",
            ),
            models.Index(
                fields=["can_view"],
                name="objectperm_can_view_idx",
            ),
            models.Index(
                fields=["can_edit"],
                name="objectperm_can_edit_idx",
            ),
        ]

    def __str__(self):
        target = self.user.username if self.user else self.group.name
        perms = []
        if self.can_view:
            perms.append("view")
        if self.can_edit:
            perms.append("edit")
        return f"{target} can {'+'.join(perms)} {self.content_type.model} #{self.object_id}"


class PermissionMixin(models.Model):
    """
    Mixin to add to models that need object-level permissions
    """

    permissions = GenericRelation(ObjectPermission)

    class Meta:
        abstract = True

    def get_permissions_for_user(self, user):
        """Get permissions for a specific user"""
        if user.is_superuser:
            return {"can_view": True, "can_edit": True}

        # Check for empty permissions - means open to all
        if self.permissions.count() == 0:
            return {"can_view": True, "can_edit": False}

        # Direct user permissions
        user_perms = self.permissions.filter(user=user)

        # Group permissions
        group_perms = self.permissions.filter(group__in=user.groups.all())

        # Combine permissions
        can_view = user_perms.filter(can_view=True).exists() or group_perms.filter(can_view=True).exists()
        can_edit = user_perms.filter(can_edit=True).exists() or group_perms.filter(can_edit=True).exists()

        return {"can_view": can_view, "can_edit": can_edit}

    def user_can_view(self, user):
        """Check if user can view this object"""
        if user.is_superuser:
            return True
        if self.permissions.count() == 0:
            return True
        perms = self.get_permissions_for_user(user)
        return perms["can_view"]

    def user_can_edit(self, user):
        """Check if user can edit this object"""
        if user.is_superuser:
            return True
        if self.permissions.count() == 0:
            return False
        perms = self.get_permissions_for_user(user)
        return perms["can_edit"]


class PostgreSQLPermissionQuerySet(models.QuerySet):
    """
    Permission QuerySet optimized for PostgreSQL using Exists subqueries
    """

    def viewable_by(self, user):
        """Return only objects viewable by the user - PostgreSQL optimized"""
        if user.is_superuser:
            return self

        content_type_id = ContentType.objects.get_for_model(self.model).id

        # PostgreSQL optimized version using Exists subqueries
        no_perms = ~Exists(
            ObjectPermission.objects.filter(
                content_type_id=content_type_id,
                object_id=OuterRef("pk"),
            ),
        )

        # User view permissions
        user_view_perms = Exists(
            ObjectPermission.objects.filter(
                content_type_id=content_type_id,
                object_id=OuterRef("pk"),
                user=user,
                can_view=True,
            ),
        )

        # Group view permissions
        if user.groups.exists():
            group_ids = user.groups.values_list("id", flat=True)
            group_view_perms = Exists(
                ObjectPermission.objects.filter(
                    content_type_id=content_type_id,
                    object_id=OuterRef("pk"),
                    group_id__in=group_ids,
                    can_view=True,
                ),
            )
            return self.filter(no_perms | user_view_perms | group_view_perms)
        return self.filter(no_perms | user_view_perms)

    def editable_by(self, user):
        """Return only objects editable by the user - PostgreSQL optimized"""
        if user.is_superuser:
            return self

        content_type_id = ContentType.objects.get_for_model(self.model).id

        # User edit permissions
        user_edit_perms = Exists(
            ObjectPermission.objects.filter(
                content_type_id=content_type_id,
                object_id=OuterRef("pk"),
                user=user,
                can_edit=True,
            ),
        )

        # Group edit permissions
        if user.groups.exists():
            group_ids = user.groups.values_list("id", flat=True)
            group_edit_perms = Exists(
                ObjectPermission.objects.filter(
                    content_type_id=content_type_id,
                    object_id=OuterRef("pk"),
                    group_id__in=group_ids,
                    can_edit=True,
                ),
            )
            return self.filter(user_edit_perms | group_edit_perms)
        return self.filter(user_edit_perms)


class SQLitePermissionQuerySet(models.QuerySet):
    """
    Permission QuerySet compatible with SQLite using simpler query methods
    """

    def viewable_by(self, user):
        """Return only objects viewable by the user - SQLite compatible"""
        if user.is_superuser:
            return self

        content_type_id = ContentType.objects.get_for_model(self.model).id

        # Objects with no permissions are viewable by all
        objects_with_perms = (
            ObjectPermission.objects.filter(
                content_type_id=content_type_id,
            )
            .values_list("object_id", flat=True)
            .distinct()
        )

        # Objects without permissions
        no_perms_q = ~Q(pk__in=objects_with_perms)

        # User permissions
        user_perms_objects = ObjectPermission.objects.filter(
            content_type_id=content_type_id,
            user=user,
            can_view=True,
        ).values_list("object_id", flat=True)

        # Group permissions
        if user.groups.exists():
            group_perms_objects = ObjectPermission.objects.filter(
                content_type_id=content_type_id,
                group__in=user.groups.all(),
                can_view=True,
            ).values_list("object_id", flat=True)

            return self.filter(
                no_perms_q | Q(pk__in=user_perms_objects) | Q(pk__in=group_perms_objects),
            )
        return self.filter(
            no_perms_q | Q(pk__in=user_perms_objects),
        )

    def editable_by(self, user):
        """Return only objects editable by the user - SQLite compatible"""
        if user.is_superuser:
            return self

        content_type_id = ContentType.objects.get_for_model(self.model).id

        # User permissions
        user_perms_objects = ObjectPermission.objects.filter(
            content_type_id=content_type_id,
            user=user,
            can_edit=True,
        ).values_list("object_id", flat=True)

        # Group permissions
        if user.groups.exists():
            group_perms_objects = ObjectPermission.objects.filter(
                content_type_id=content_type_id,
                group__in=user.groups.all(),
                can_edit=True,
            ).values_list("object_id", flat=True)

            return self.filter(
                Q(pk__in=user_perms_objects) | Q(pk__in=group_perms_objects),
            )
        return self.filter(Q(pk__in=user_perms_objects))

    def accessible_by(self, user):
        """Objects viewable OR editable by user."""
        if not user.is_authenticated:
            return self.none()

        if user.is_superuser:
            return self

        content_type = ContentType.objects.get_for_model(self.model)

        user_perms = Q(permissions__user=user)
        group_perms = Q(permissions__group__in=user.groups.all()) if user.groups.exists() else Q()

        permission_filter = Q(
            permissions__content_type=content_type,
            permissions__can_view=True,
        ) | Q(
            permissions__content_type=content_type,
            permissions__can_edit=True,
        )

        return self.filter(permission_filter & (user_perms | group_perms)).distinct()

    def editable_ids_by(self, user):
        """List of IDs user can edit."""
        if not user.is_authenticated:
            return []

        if user.is_superuser:
            return list(self.values_list("id", flat=True))

        content_type = ContentType.objects.get_for_model(self.model)

        user_perms = Q(permissions__user=user)
        group_perms = Q(permissions__group__in=user.groups.all()) if user.groups.exists() else Q()

        return list(
            self.filter(
                Q(permissions__content_type=content_type),
                Q(permissions__can_edit=True),
                user_perms | group_perms,
            ).values_list("id", flat=True),
        )


PermissionQuerySet = PostgreSQLPermissionQuerySet if settings.IS_POSTGRESQL else SQLitePermissionQuerySet


class PermissionManager(models.Manager):
    def get_queryset(self):
        return PermissionQuerySet(self.model, using=self._db)

    def viewable_by(self, user):
        return self.get_queryset().viewable_by(user)

    def editable_by(self, user):
        return self.get_queryset().editable_by(user)

    def accessible_by(self, user):
        return self.get_queryset().accessible_by(user)

    def editable_ids_by(self, user):
        return self.get_queryset().editable_ids_by(user)
