import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from memoria.models import Image
from memoria.views.mixins import DefaultPaginationMixin
from memoria.views.mixins import ObjectPermissionViewMixin

User = get_user_model()

logger = logging.getLogger(__name__)


class ImageListView(LoginRequiredMixin, ObjectPermissionViewMixin, DefaultPaginationMixin, ListView):
    model = Image
    template_name = "images/list.html.jinja"
    context_object_name = "images"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "All Images"

        context["editable_images"] = self.queryset.filter(can_edit=True)

        return context


class ImageDetailView(LoginRequiredMixin, ObjectPermissionViewMixin, DetailView):
    model = Image
    template_name = "images/detail.html.jinja"
    context_object_name = "image"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add additional context data, including whether the user can edit the image.
        """
        context = super().get_context_data(**kwargs)

        user = self.request.user
        obj = self.object

        # Check if user can edit this object using the filter_editable method.
        # This is the efficient and recommended way using your AccessQuerySet.
        context["can_edit"] = Image.objects.filter_editable(user).filter(pk=obj.pk).exists()

        return context


class ImageUpdateView(LoginRequiredMixin, UpdateView):
    model = Image
    template_name = "images/update.html.jinja"

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful update.
        """
        return reverse("image-detail", kwargs={"pk": self.object.pk})

    def get_queryset(self) -> QuerySet[Image]:
        """
        Override to return only objects the user has explicit edit access to.
        This leverages the AccessQuerySet's filter_editable method.
        """
        # Use the filter_editable method to efficiently filter for editable objects.
        # This automatically handles superusers and group-based edit permissions.
        return Image.objects.filter_editable(self.request.user)
