from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class PeopleView(LoginRequiredMixin, TemplateView):
    template_name = "people.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "People"
        return context
