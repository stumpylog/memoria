from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from memoria.models import UserProfile

User = get_user_model()


class UserEmailForm(forms.ModelForm):
    """Form for updating the user's email address."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating the user's profile details (bio, images per page)."""

    class Meta:
        model = UserProfile
        fields = ("bio", "items_per_page", "timezone")


class GroupMembershipForm(forms.Form):
    """
    Form to manage a user's group memberships.
    """

    # Queryset should include all available groups
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Render as checkboxes
        required=False,  # User doesn't have to be in any group
        label=None,
    )

    # We might need to pass the user instance to the form
    # to set the initial values, but ModelForm handles that.
    # For a standard Form, we'll set initial in the view.

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.pop("user", None)  # Get the user instance
        super().__init__(*args, **kwargs)
        if user_instance:
            # Set initial value based on the user's current groups
            self.fields["groups"].initial = user_instance.groups.all()
