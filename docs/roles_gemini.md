# Role-Based Access Control (RBAC) Design

From Gemini 2.5 Pro

This document outlines the design for an RBAC system using Django, `django-guardian`, and standard Django authentication components (`User`, `Group`, `Permission`).

## 1. Core Concepts & Requirements

- **Authentication:** Standard Django `User` model. Users must be `is_active` to perform actions.
- **Authorization:** Group-based. Users inherit permissions from the `Group`s they belong to.
- **Object-Level Permissions:** Permissions are granular, assigned per specific instance of `Image`, `ImageFolder`, `Person`, `Pet`, `ImageSource`, or `Album`.
- **Permission Types:** `view` and `edit`. Editing implies viewing.
- **Groups:** Represent logical units (e.g., "Holmes Family", "Watson Family"). Specific groups might grant view ("Holmes View") or edit ("Holmes Edit") access.
- **Superusers:** Have unrestricted access (`user.is_superuser`).
- **Staff Users:** Can manage `User` and `Group` objects (`user.is_staff`). Only superusers can grant staff status.
- **Public Access:** Objects with _no_ explicitly assigned view or edit permissions are considered public and accessible (view/edit) by any authenticated, active user.
- **Related Objects:** Accessing container objects (e.g., `Album`) must also filter their related items (e.g., `Images`) based on the user's permissions for those related items.
- **Technology:** Django, `django-guardian`, PostgreSQL/SQLite, Class-Based Views (CBVs), Jinja2, Bootstrap 5, Python Type Hinting, `pathlib`.
- **Performance:** Prioritize database-level filtering, use `select_related`/`prefetch_related`, consider caching.

## 2. Setup & Dependencies

1.  **Install `django-guardian`:**

    ```bash
    pip install django-guardian
    ```

2.  **Add to `settings.py`:**

    ```python
    # settings.py
    INSTALLED_APPS = [
        # ... other apps
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'guardian', # Add guardian
        # ... your apps (e.g., 'photos')
    ]

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend', # Default Django auth
        'guardian.backends.ObjectPermissionBackend', # Guardian object permissions
    )

    # Optional: Define anonymous user name if needed by guardian
    # ANONYMOUS_USER_NAME = None
    ```

3.  **Run migrations:**
    ```bash
    python manage.py migrate
    ```

## 3. Model & Permission Design

We'll use the standard Django `User`, `Group`, and `Permission` models. `django-guardian` adds `UserObjectPermission` and `GroupObjectPermission` tables behind the scenes to link permissions to specific object instances.

- **Permissions:** We will use the standard `view_<modelname>` and `change_<modelname>` permissions automatically created by Django for each model.
  - `view_<modelname>` maps to our "view" requirement.
  - `change_<modelname>` maps to our "edit" requirement.
- **Groups:** Create groups that represent access levels. Examples:
  - `Holmes View`: Grants view permissions to specific objects.
  - `Holmes Edit`: Grants change (edit) permissions to specific objects.
  - A user might be in both `Holmes View` and `Holmes Edit`.

!!! note
Assigning `change_<modelname>` permission to a group for an object implicitly grants `view_<modelname>` access as well when using `django-guardian`'s helpers like `get_objects_for_user`.

- **Assigning Permissions:** Permissions will be assigned to _Groups_ for specific object instances.

  ```python
  from django.contrib.auth.models import Group
  from guardian.shortcuts import assign_perm
  from .models import Image, Album # Assuming models are in the same app

  # Example: Grant 'Holmes View' group permission to view a specific image
  holmes_view_group = Group.objects.get(name='Holmes View')
  image_instance = Image.objects.get(pk=1)
  assign_perm('photos.view_image', holmes_view_group, image_instance)

  # Example: Grant 'Holmes Edit' group permission to change a specific album
  holmes_edit_group = Group.objects.get(name='Holmes Edit')
  album_instance = Album.objects.get(pk=5)
  assign_perm('photos.change_album', holmes_edit_group, album_instance)
  ```

## 4. Helper Functions for Querying

To handle the complex logic (explicit permissions OR public access) and keep views clean, let's create helper functions.

```python
# photos/permissions.py
from typing import Type, TypeVar, Union, List, Optional
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, QuerySet
from guardian.shortcuts import get_objects_for_user
from guardian.models import GroupObjectPermission, UserObjectPermission

T = TypeVar('T', bound=models.Model)

def get_viewable_objects(user: User, queryset: QuerySet[T], model_cls: Type[T]) -> QuerySet[T]:
    """
    Returns a queryset of objects the user can view.

    Includes objects where:
    1. The user has explicit 'view' or 'change' permission (via group or direct).
    2. The object has NO 'view' permissions assigned to *any* group or user
       (meaning it's public).
    """
    if not user.is_authenticated or not user.is_active:
        return queryset.none()

    if user.is_superuser:
        return queryset

    app_label = model_cls._meta.app_label
    model_name = model_cls._meta.model_name
    view_perm = f'{app_label}.view_{model_name}'
    change_perm = f'{app_label}.change_{model_name}'

    # 1. Objects user has explicit view/change permission for
    # 'any_perm=True' means user gets obj if they have EITHER view OR change perm
    explicitly_allowed_pks = get_objects_for_user(
        user,
        [view_perm, change_perm],
        klass=model_cls,
        any_perm=True,
        use_groups=True,
        with_superuser=False # Already handled superuser case
    ).values_list('pk', flat=True)

    # 2. Objects with NO 'view' permissions set for anyone (public)
    # Get ContentType for the model
    content_type = ContentType.objects.get_for_model(model_cls)

    # Find PKs of objects that HAVE group or user view permissions assigned
    pks_with_group_view_perms = GroupObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'view_{model_name}',
        permission__content_type=content_type # Ensure correct permission
    ).values_list('object_pk', flat=True)

    pks_with_user_view_perms = UserObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'view_{model_name}',
        permission__content_type=content_type # Ensure correct permission
    ).values_list('object_pk', flat=True)

    # Combine and distinct
    pks_with_any_view_perms = set(pks_with_group_view_perms) | set(pks_with_user_view_perms)

    # Convert pks_with_any_view_perms to the correct type if necessary (e.g., int, str)
    # Assuming primary keys are integers for simplicity here. Adjust if UUIDs etc.
    pks_with_any_view_perms_int = {int(pk) for pk in pks_with_any_view_perms if pk}

    # Build the combined query
    combined_filter = Q(pk__in=list(explicitly_allowed_pks)) | ~Q(pk__in=pks_with_any_view_perms_int)

    return queryset.filter(combined_filter).distinct()


def get_editable_objects(user: User, queryset: QuerySet[T], model_cls: Type[T]) -> QuerySet[T]:
    """
    Returns a queryset of objects the user can edit.

    Includes objects where:
    1. The user has explicit 'change' permission (via group or direct).
    2. The object has NO 'change' permissions assigned to *any* group or user
       (meaning it's publicly editable).
    """
    if not user.is_authenticated or not user.is_active:
        return queryset.none()

    if user.is_superuser:
        return queryset

    app_label = model_cls._meta.app_label
    model_name = model_cls._meta.model_name
    change_perm = f'{app_label}.change_{model_name}'

    # 1. Objects user has explicit change permission for
    explicitly_editable_pks = get_objects_for_user(
        user,
        change_perm, # Only check for change permission
        klass=model_cls,
        use_groups=True,
        with_superuser=False
    ).values_list('pk', flat=True)

    # 2. Objects with NO 'change' permissions set for anyone (publicly editable)
    content_type = ContentType.objects.get_for_model(model_cls)

    # Find PKs of objects that HAVE group or user change permissions assigned
    pks_with_group_change_perms = GroupObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'change_{model_name}',
        permission__content_type=content_type
    ).values_list('object_pk', flat=True)

    pks_with_user_change_perms = UserObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'change_{model_name}',
        permission__content_type=content_type
    ).values_list('object_pk', flat=True)

    pks_with_any_change_perms = set(pks_with_group_change_perms) | set(pks_with_user_change_perms)
    pks_with_any_change_perms_int = {int(pk) for pk in pks_with_any_change_perms if pk}

    # Build the combined query
    combined_filter = Q(pk__in=list(explicitly_editable_pks)) | ~Q(pk__in=pks_with_any_change_perms_int)

    return queryset.filter(combined_filter).distinct()


def check_object_view_permission(user: User, obj: T) -> bool:
    """Checks if a user can view a specific object."""
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True

    model_cls = type(obj)
    app_label = model_cls._meta.app_label
    model_name = model_cls._meta.model_name
    view_perm = f'{app_label}.view_{model_name}'
    change_perm = f'{app_label}.change_{model_name}'

    # Check explicit permissions first
    if user.has_perm(view_perm, obj) or user.has_perm(change_perm, obj):
        return True

    # Check if the object is public (no view permissions assigned)
    content_type = ContentType.objects.get_for_model(model_cls)
    has_any_view_permission = GroupObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'view_{model_name}',
        permission__content_type=content_type,
        object_pk=obj.pk
    ).exists() or UserObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'view_{model_name}',
        permission__content_type=content_type,
        object_pk=obj.pk
    ).exists()

    return not has_any_view_permission


def check_object_edit_permission(user: User, obj: T) -> bool:
    """Checks if a user can edit a specific object."""
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True

    model_cls = type(obj)
    app_label = model_cls._meta.app_label
    model_name = model_cls._meta.model_name
    change_perm = f'{app_label}.change_{model_name}'

    # Check explicit permission first
    if user.has_perm(change_perm, obj):
        return True

    # Check if the object is publicly editable (no change permissions assigned)
    content_type = ContentType.objects.get_for_model(model_cls)
    has_any_change_permission = GroupObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'change_{model_name}',
        permission__content_type=content_type,
        object_pk=obj.pk
    ).exists() or UserObjectPermission.objects.filter(
        content_type=content_type,
        permission__codename=f'change_{model_name}',
        permission__content_type=content_type,
        object_pk=obj.pk
    ).exists()

    return not has_any_change_permission
```
