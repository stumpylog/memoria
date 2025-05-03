from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.views.generic import DetailView
from django.views.generic import ListView

from memoria.models import ImageFolder


class ImageFolderListView(LoginRequiredMixin, ListView):
    """
    List view to display all ImageFolder objects, ordered by name.
    """

    model = ImageFolder
    template_name = "folders/list.html.jinja"  # Or your template path
    context_object_name = "folders"  # Name for the list of objects in the template

    def get_queryset(self) -> QuerySet[ImageFolder]:
        """
        Return the queryset for the view, getting only accessible root folders, ordered by name.
        """
        root_folders_qs: QuerySet[ImageFolder] = ImageFolder.get_roots_queryset()
        accessible_folders_qs: QuerySet[ImageFolder] = ImageFolder.permissions_manager.accessible_by(self.request.user)

        return (
            root_folders_qs.filter(pk__in=accessible_folders_qs.values("pk"))
            .order_by("name")
            .prefetch_related("images")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Image Folders"
        return context


class ImageFolderDetailView(LoginRequiredMixin, DetailView):
    model = ImageFolder
    template_name = "folders/detail.html.jinja"
    context_object_name = "folder"

    def get_queryset(self) -> QuerySet[ImageFolder]:
        """
        Return the queryset for the view, ensuring the folder is accessible.
        The DetailView will then filter this queryset by PK from the URL.
        """
        # Start with only folders accessible by the current user
        queryset: QuerySet[ImageFolder] = ImageFolder.permissions_manager.accessible_by(self.request.user)
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add additional context data for the template, like child folders and images.
        """
        context = super().get_context_data(**kwargs)

        context["title"] = self.object.name

        # Get child folders accessible by the current user, ordered by name
        # We filter the object's children by checking if their PK is in the accessible set
        accessible_children_qs = ImageFolder.permissions_manager.accessible_by(self.request.user)
        context["child_folders"] = (
            self.object.get_children_queryset()
            .filter(
                pk__in=accessible_children_qs.values("pk"),
            )
            .order_by("name")
        )

        # Get images related to this folder that are accessible by the current user
        # Assuming your Image model also has a permissions_manager or similar
        # If not, you might need a different way to check image permissions
        # For simplicity, we'll assume image permissions are tied to folder permissions
        # If images have their own permissions, you'd need a similar filter here.
        # Example (assuming Image model has permissions_manager):
        # accessible_images_qs = Image.permissions_manager.accessible_by(self.request.user)
        # context['images'] = self.object.images.filter(
        #     pk__in=accessible_images_qs.values('pk')
        # ).order_by('name') # Or by upload date, etc.

        # For now, let's just get all images related to this folder
        # IMPORTANT: If images have separate permissions, this needs refinement!
        context["images"] = self.object.images.all().order_by("original_name")  # Or another field

        return context
