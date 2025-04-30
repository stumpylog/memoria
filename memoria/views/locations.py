from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class LocationsView(LoginRequiredMixin, TemplateView):
    template_name = "locations.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Locations"
        return context
