import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from memoria.models import Image
from memoria.models import UserProfile

User = get_user_model()

logger = logging.getLogger(__name__)


class ImagesView(LoginRequiredMixin, ListView):
    model = Image
    default_paginate_by = UserProfile.ImagesPerPageChoices.THIRTY
    template_name = "images.html.jinja"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "All Images"

        return context

    def get_paginate_by(self, queryset) -> int:  # noqa: ARG002
        """
        Dynamically determine paginate_by based on user profile.
        """
        user: User = self.request.user

        try:
            # Assuming your User has a one-to-one field named 'profile'
            # that links to your Profile model, and Profile has a field
            # 'items_per_page'. Adjust attribute names as needed.
            profile: UserProfile = user.profile
            user_preference: int = profile.images_per_page

            # Basic validation: ensure the preference is a positive integer
            if isinstance(user_preference, int) and user_preference > 0:
                return user_preference
            # Handle cases where the preference is invalid
            logger.warning(
                f"Invalid pagination preference ({user_preference}) for user {user.username}. Using default.",
            )

        except UserProfile.DoesNotExist:
            # Handle the case where the user does not have a profile
            logger.warning(f"Profile not found for user {user.username}. Using default paginate_by.")
        except AttributeError:
            # Handle case if the 'items_per_page' field doesn't exist on the Profile
            logger.warning(
                f"'items_per_page' field not found on Profile for user {user.username}. Using default paginate_by.",
            )
        except Exception:
            # Catch any other potential errors during profile access
            logger.exception(f"Error accessing profile pagination preference for user {user.username}: Using default.")

        # If the user is not authenticated (though LoginRequiredMixin should prevent this)
        # or if profile access fails, fall back to the default
        return self.default_paginate_by
