import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView

from memoria.forms import PersonForm
from memoria.models import Image
from memoria.models import Person
from memoria.models import UserProfile

logger = logging.getLogger(__name__)
User = get_user_model()


class PeopleListView(LoginRequiredMixin, ListView):
    template_name = "people/list.html.jinja"
    model = Person
    default_paginate_by = UserProfile.ImagesPerPageChoices.THIRTY

    def get_queryset(self):
        # TODO: Need to filter by what a user can see
        return Person.objects.annotate(images_count=Count("images")).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "People"
        return context

    def get_paginate_by(self, queryset) -> int:  # noqa: ARG002
        """
        Dynamically determine paginate_by based on user profile.

        # TODO: Need to use a new field here?  Or rename the old one
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


class PersonDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for the Person model.

    Displays the details of a single person based on the primary key in the URL.
    Handles GET requests to display the person's details and a form,
    and POST requests to process the form submission and update the person.
    Uses the redirect shortcut.
    """

    model: type[Person] = Person
    template_name: str = "people/detail.html.jinja"
    form_class: type[PersonForm] = PersonForm  # Define the form class

    def get_context_data(self, **kwargs) -> dict:
        """
        Add the form and session-stored errors to the context.
        """
        context = super().get_context_data(**kwargs)
        person = self.get_object()

        # Retrieve form errors from the session and add them to the context
        edit_person_form_data = self.request.session.pop("edit_person_form_data", None)

        edit_person_form = (
            PersonForm(edit_person_form_data, instance=person) if edit_person_form_data else PersonForm(instance=person)
        )
        context["edit_person_form"] = edit_person_form

        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:  # noqa: ARG002
        """
        Handle POST requests for form submission.
        """
        self.object = self.get_object()  # Get the Person instance

        # Instantiate the form with POST data and the instance
        form = self.form_class(request.POST, instance=self.object)

        redirect_url = reverse("person_detail", kwargs={"pk": self.object.pk})

        if form.is_valid():
            # Save the form if valid (updates the Person instance)
            form.save()
        else:
            request.session["edit_person_form_data"] = request.POST
            messages.error(request, "Error editing person. Please check the form.")  # Generic error message
        return redirect(redirect_url)


class PersonPhotosListView(LoginRequiredMixin, ListView):
    template_name = "people/photos.html.jinja"
    model = Image
    # TODO: Grab from the profile
    paginate_by = UserProfile.ImagesPerPageChoices.THIRTY

    def get_queryset(self) -> QuerySet:
        """
        Returns the queryset of images filtered by the person's primary key
        from the URL.
        """
        queryset = super().get_queryset()

        # Get the person_id from the URL kwargs
        person_pk = self.kwargs.get("pk")

        # TODO: Also filter to only the images a user can view

        return queryset.filter(people__pk=person_pk) if person_pk else queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person_pk = self.kwargs.get("pk")
        context["person"] = Person.objects.get(pk=person_pk)
        return context
