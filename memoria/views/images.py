import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpRequest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from simpleiso3166 import ALPHA2_CODE_TO_COUNTRIES

from memoria.forms import ImageUpdateForm
from memoria.models import Image
from memoria.models import RoughLocation
from memoria.utils.geo import get_country_list_for_autocomplete
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


# TODO: Make login required
def ajax_get_subdivisions(request: HttpRequest):
    country_code = request.GET.get("country_code", None)
    if not country_code:
        return JsonResponse([], safe=False)

    country_data = ALPHA2_CODE_TO_COUNTRIES.get(country_code)
    if country_data:
        return JsonResponse(
            [{"value": subdivision.code, "label": subdivision.name} for subdivision in country_data.subdivisions],
            safe=False,
        )

    return JsonResponse([], safe=False)


def ajax_get_cities(request: HttpRequest):
    """
    AJAX endpoint to fetch city suggestions for autocomplete.

    Required query parameters:
    - country_code: The ISO country code

    Optional query parameters:
    - subdivision_code: The ISO subdivision code
    - q: Search term for filtering results

    Returns:
    - JSON array of {value, label} objects for Choices.js
    """
    country_code = request.GET.get("country_code")
    subdivision_code = request.GET.get("subdivision_code")
    search_query = request.GET.get("q", "").strip()

    if not country_code:
        return JsonResponse([], safe=False)

    # Build query to filter unique cities
    query = Q(country_code=country_code)

    if subdivision_code:
        query &= Q(subdivision_code=subdivision_code)

    # Only include cities that aren't null or empty
    query &= ~Q(city__isnull=True) & ~Q(city="")

    # Add search filter if provided
    if search_query:
        query &= Q(city__icontains=search_query)

    # Get distinct cities (case-insensitive)
    cities = RoughLocation.objects.filter(query).values_list("city", flat=True).distinct()

    # Sort cities alphabetically and convert to choices format
    cities_list = sorted(set(cities), key=lambda x: x.lower())
    choices = [{"value": city, "label": city} for city in cities_list]

    return JsonResponse(choices, safe=False)


def ajax_get_sub_locations(request: HttpRequest):
    """
    AJAX endpoint to fetch sub-location suggestions for autocomplete.

    Required query parameters:
    - country_code: The ISO country code
    - city: The city name

    Optional query parameters:
    - subdivision_code: The ISO subdivision code
    - q: Search term for filtering results

    Returns:
    - JSON array of {value, label} objects for Choices.js
    """
    country_code = request.GET.get("country_code")
    subdivision_code = request.GET.get("subdivision_code")
    city = request.GET.get("city")
    search_query = request.GET.get("q", "").strip()

    if not country_code or not city:
        return JsonResponse([], safe=False)

    # Build query to filter unique sub-locations
    query = Q(country_code=country_code) & Q(city=city)

    if subdivision_code:
        query &= Q(subdivision_code=subdivision_code)

    # Only include sub_locations that aren't null or empty
    query &= ~Q(sub_location__isnull=True) & ~Q(sub_location="")

    # Add search filter if provided
    if search_query:
        query &= Q(sub_location__icontains=search_query)

    # Get distinct sub_locations (case-insensitive)
    sub_locations = RoughLocation.objects.filter(query).values_list("sub_location", flat=True).distinct()

    # Sort sub_locations alphabetically and convert to choices format
    sub_locations_list = sorted(set(sub_locations), key=lambda x: x.lower())
    choices = [{"value": loc, "label": loc} for loc in sub_locations_list]

    return JsonResponse(choices, safe=False)
