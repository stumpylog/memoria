from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView

from memoria.models import Image


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = "home.html.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        base_qs = Image.objects.all()

        if user.is_superuser:
            # Superusers see all images and can edit all
            img_filter = Q()
        else:
            groups = user.groups.all()

            # No groups set, anyone can access
            open_to_all_filter = Q(edit_groups__isnull=True) & Q(view_groups__isnull=True)
            # User is in the one or more view groups
            can_view_filter = Q(view_groups__in=groups)
            # User is in one or more edit groups
            can_edit_filter = Q(edit_groups__in=groups)

            img_filter = open_to_all_filter | can_view_filter | can_edit_filter

        images = base_qs.filter(img_filter).distinct().order_by("-created_at")[:20]

        context["title"] = "Home"
        context["message"] = "Check out your recent images below."
        context["recent_images"] = images
        return context
