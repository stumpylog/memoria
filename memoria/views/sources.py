from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from memoria.models import Image


class SourcesView(LoginRequiredMixin, TemplateView):
    template_name = "sources.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Galleries"

        context["images"] = list(Image.objects.all())

        return context
