import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import ExtractYear
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from memoria.forms import ImageUpdateForm
from memoria.models import Image
from memoria.models import RoughDate
from memoria.utils.geo import get_country_list_for_autocomplete
from memoria.utils.geo import get_subdivisions_for_country_for_autocomplete
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
    permission_type = "view"
    template_name = "images/detail.html.jinja"
    context_object_name = "image"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "folder",
            "source",
            "location",
            "date",
        ).prefetch_related(
            "people",
            "pets",
            "tags",
            "personinimage_set__person",
            "petinimage_set__pet",
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add additional context data, including whether the user can edit the image.
        """
        context = super().get_context_data(**kwargs)

        context["can_edit"] = self.has_object_permission(self.object)["can_edit"]

        return context


class ImageUpdateView(LoginRequiredMixin, ObjectPermissionViewMixin, UpdateView):
    model = Image
    form_class = ImageUpdateForm
    template_name = "images/update.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Data for RoughDate year autocomplete (existing years from DB)
        # Providing a list of all unique years found in RoughDate objects
        context["available_years_for_choicesjs"] = list(
            RoughDate.objects.annotate(year_val=ExtractYear("date")).distinct().values_list("year_val", flat=True),
        )
        # Data for RoughLocation country autocomplete
        context["available_countries_for_choicesjs"] = get_country_list_for_autocomplete()

        image_update_form_data = self.request.session.pop("image_update_form_data", None)

        if image_update_form_data:
            # Instantiate form with data and errors from session and the user instance
            image_update_form = ImageUpdateForm(image_update_form_data, instance=self.object)
        else:
            # No data in session, provide a new unbound form for the user instance
            image_update_form = ImageUpdateForm(instance=self.object)

        context["form"] = image_update_form

        # Subdivisions will be loaded via AJAX, so no initial list here.
        return context

    def post(self, request, pk: int, *args, **kwargs):
        image = get_object_or_404(Image, pk=pk)
        form = ImageUpdateForm(request.POST, instance=image)

        if form.is_valid():
            form.save()
            messages.success(request, "Image updated successfully.")
            return redirect(reverse("image_detail", kwargs={"pk": image.pk}))

        # invalid: stash the POST data and show generic error
        request.session["image_update_form_data"] = request.POST
        messages.error(request, "There were errors in your submission; please correct them below.")
        return redirect(reverse("image_update", kwargs={"pk": image.pk}))


def get_subdivisions_ajax(request):
    country_code = request.GET.get("country_code", None)
    if not country_code:
        return JsonResponse([], safe=False)  # Return empty list if no country code

    subdivisions_list = get_subdivisions_for_country_for_autocomplete(country_code)
    return JsonResponse(subdivisions_list, safe=False)
