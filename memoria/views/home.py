from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from memoria.models import Image


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = "home.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        if user.is_superuser:
            # Superusers see all images and can edit all
            images = Image.objects.all().order_by("-created_at")[:20]
            context["all_editable"] = True
        else:
            images = Image.get_accessible_objects(self.request.user, ImagePermission.VIEW).order_by("-created_at")[:20]
            editable_ids = (
                Image.get_accessible_objects(self.request.user, ImagePermission.CHANGE)
                .only("pk")
                .distinct()
                .values_list("pk", flat=True)
            )
            context["editable_image_ids"] = editable_ids

        context["title"] = "Home"
        context["message"] = "Check out your recent images below."
        context["recent_images"] = images
        return context
