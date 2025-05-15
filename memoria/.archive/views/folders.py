import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView

from memoria.models import Image
from memoria.models import ImageFolder
from memoria.views.mixins import DefaultPaginationMixin
from memoria.views.mixins import ObjectPermissionViewMixin

logger = logging.getLogger(__name__)


class ImageFolderListView(LoginRequiredMixin, DefaultPaginationMixin, ObjectPermissionViewMixin, ListView):
    """
    List view to display accessible root ImageFolder objects, ordered by name,
    with image counts per folder. Uses ObjectPermissionViewMixin for base filtering.
    """

    model = ImageFolder
    template_name = "folders/list.html.jinja"
    context_object_name = "folders"

    def get_queryset(self):
        user = self.request.user
        groups = user.groups.all()

        # Filter only root folders
        roots = ImageFolder.get_roots_queryset().values_list("pk", flat=True)
        base_qs = super().get_queryset().filter(pk__in=roots).order_by("name")

        # Permission filter for both subqueries
        if user.is_superuser:
            perm_filter = Q()
        else:
            perm_filter = Q(view_groups__isnull=True) | Q(view_groups__in=groups) | Q(edit_groups__in=groups)

        # Subquery: count direct child folders with permission check
        children_qs = (
            ImageFolder.objects.filter(
                Q(tn_parent=OuterRef("pk")) & perm_filter,
            )
            .values("tn_parent")
            .annotate(count=Count("pk", distinct=True))
            .values("count")
        )

        # Subquery: count direct images in folder with permission check
        image_qs = (
            Image.objects.filter(
                Q(folder=OuterRef("pk")) & perm_filter,
            )
            .values("folder")
            .annotate(count=Count("pk", distinct=True))
            .values("count")
        )

        # Annotate counts using subqueries with proper coalescing
        return base_qs.annotate(
            child_count=Coalesce(Subquery(children_qs), 0),
            image_count=Coalesce(Subquery(image_qs), 0),
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["title"] = "Image Folders"

        return context


class ImageFolderDetailView(LoginRequiredMixin, ObjectPermissionViewMixin, DetailView):
    model = ImageFolder
    permission_type = "view"
    template_name = "folders/detail.html.jinja"
    context_object_name = "folder"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder = self.get_object()
        user = self.request.user
        groups = user.groups.all()

        context["title"] = folder.name

        # Permission filter for subqueries based on user groups
        if user.is_superuser:
            perm_filter = Q()
        else:
            perm_filter = Q(view_groups__isnull=True) | Q(view_groups__in=groups) | Q(edit_groups__in=groups)

        # Get child folders of the current folder with permission checks
        # And annotate each child folder with the count of its own children and images.
        child_folders = ImageFolder.objects.filter(tn_parent=folder).order_by("name")

        # Apply permission filter to the child folders queryset itself
        if not user.is_superuser:
            child_folders = child_folders.filter(perm_filter).distinct()

        # Subquery to count direct child folders for EACH child folder with permission check
        children_qs = (
            ImageFolder.objects.filter(
                Q(tn_parent=OuterRef("pk")) & perm_filter,
            )
            .values("tn_parent")
            .annotate(count=Count("pk", distinct=True))
            .values("count")
        )

        # Subquery to count direct images for EACH child folder with permission check
        image_qs = (
            Image.objects.filter(
                Q(folder=OuterRef("pk")) & perm_filter,
            )
            .values("folder")
            .annotate(count=Count("pk", distinct=True))
            .values("count")
        )

        # Annotate the child_folders queryset with the counts
        child_folders = child_folders.annotate(
            child_folder_count=Coalesce(Subquery(children_qs), 0),
            image_count=Coalesce(Subquery(image_qs), 0),
        )

        # Get images directly in the current folder with permission checks (as before)
        image_queryset = Image.objects.filter(folder=folder)
        if not user.is_superuser:
            image_queryset = image_queryset.filter(
                Q(view_groups__isnull=True) | Q(view_groups__in=groups) | Q(edit_groups__in=groups),
            ).distinct()

        ancestors = list(folder.get_ancestors_queryset())
        breadcrumb_objects = [*ancestors, folder]
        breadcrumbs = [{"name": "Top", "url": reverse("image_folder_list")}]
        for obj in breadcrumb_objects:
            # Use reverse to generate the URL
            folder_url = reverse("image_folder_detail", kwargs={"pk": obj.pk})
            breadcrumbs.append({"name": obj.name, "url": folder_url})

        context.update(
            {
                "child_folders": child_folders,
                "folder_images": image_queryset,
                "has_children": child_folders.exists(),
                "image_count": image_queryset.count(),
                "breadcrumbs": breadcrumbs,
            },
        )

        return context
