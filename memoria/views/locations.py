from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import DetailView
from django.views.generic import ListView

from memoria.models import RoughLocation


class RoughLocationListView(LoginRequiredMixin, ListView):
    template_name = "locations/list.html.jinja"
    model = RoughLocation
    queryset = RoughLocation.objects.all()
    context_object_name = "images"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Rough Locations"
        return context


class RoughLocationDetailView(LoginRequiredMixin, DetailView):
    template_name = "locations/detail.html.jinja"
    model = RoughLocation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Images in {self.object!s}"

        user = self.request.user
        base_qs = self.object.images.all()
        if not user.is_active:
            context["images"] = base_qs.none()
        elif user.is_superuser:
            context["images"] = base_qs
        else:
            groups = user.groups.all()

            # No groups set, anyone can access
            open_to_all_filter = Q(edit_groups__isnull=True) & Q(view_groups__isnull=True)
            # User is in the one or more view groups
            can_view_filter = Q(view_groups__in=groups)
            # User is in one or more edit groups
            can_edit_filter = Q(edit_groups__in=groups)

            context["images"] = base_qs.filter(open_to_all_filter | can_view_filter | can_edit_filter).distinct()

        return context
