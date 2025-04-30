# your_app/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name: str = "home.html.jinja"

    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs) -> dict:
        # Call the parent class's method to get the default context
        context = super().get_context_data(**kwargs)

        # Add our specific context data
        context["title"] = "My First Django Page"
        context["message"] = "Hello from an class-based view using Bootstrap 5!"

        return context
