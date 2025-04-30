from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class AlbumsView(LoginRequiredMixin, TemplateView):
    template_name = "albums.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Albums"
        return context
