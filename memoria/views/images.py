import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from memoria.models import Image
from memoria.views.mixins import AccessQuerysetMixin
from memoria.views.mixins import DefaultPaginationMixin

User = get_user_model()

logger = logging.getLogger(__name__)


class ImageListView(LoginRequiredMixin, AccessQuerysetMixin, DefaultPaginationMixin, ListView):
    model = Image
    template_name = "images/list.html.jinja"
    context_object_name = "images"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "All Images"

        context["editable_images"] = self.queryset.filter(can_edit=True)

        return context


class ImageDetailView(LoginRequiredMixin, AccessQuerysetMixin, DetailView):
    model = Image
    template_name = "images/detail.html.jinja"
    context_object_name = "image"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Check if user can edit this object
        user = self.request.user
        obj = self.object

        if user.is_superuser:
            context["can_edit"] = True
        else:
            # Check explicit edit permission
            context["can_edit"] = self.queryset.filter(can_edit=True, pk=obj.pk).exists()

        return context


class ImageUpdateView(LoginRequiredMixin, UpdateView):
    model = Image
    template_name = "images/update.html.jinja"

    def get_success_url(self):
        return reverse("image-detail", kwargs={"pk": self.object.pk})

    def get_queryset(self):
        """
        Override to return only objects the user can edit.
        This efficiently filters at the queryset level before get_object is called.
        """
        # Reuse the existing get_accessible_objects method with the CHANGE permission
        return Image.get_accessible_objects(
            self.request.user,
            ImagePermission.CHANGE,
        )
