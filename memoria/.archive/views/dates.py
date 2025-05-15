from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DatesView(LoginRequiredMixin, TemplateView):
    template_name = "dates.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dates"
        return context
