import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()

logger = logging.getLogger(__name__)


class AddUserForm(UserCreationForm):
    """
    A form for creating new users. Includes fields for username, email, and password.
    Inherits from Django's UserCreationForm for basic user creation logic.
    """

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        required=False,  # Email might be optional depending on your User model setup
        help_text=_("Optional."),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Use default fields from UserCreationForm but add email
        fields = ("username", "email")
        # password fields are handled by UserCreationForm automatically

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with that email address already exists."))
        return email

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        # Any custom user setup can go here before saving
        if commit:
            user.save()
        return user


class AddGroupForm(forms.ModelForm):
    """
    A simple form for creating a new group.
    """

    name = forms.CharField(
        label=_("Group Name"),
        max_length=150,  # Max length for Group name in Django
        validators=[
            RegexValidator(
                r"^[ \w\.@+-]+$",
                _(
                    "Enter a valid group name. This value may contain only letters, numbers, and @/./+/-/_/ / characters.",
                ),
            ),
        ],
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_/ / only."),
    )

    class Meta:
        model = Group
        fields = ("name",)

    def clean_name(self) -> str:
        name = self.cleaned_data["name"]
        if Group.objects.filter(name=name).exists():
            raise forms.ValidationError(_("A group with that name already exists."))
        return name

    def save(self, commit: bool = True) -> Group:
        group = super().save(commit=False)
        if commit:
            group.save()
        return group


class ManageUserGroupsForm(forms.ModelForm):
    """
    Form to manage the group memberships of a specific user.
    """

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by("name"),
        widget=forms.CheckboxSelectMultiple,  # Or forms.SelectMultiple
        label=_("Groups"),
        required=False,  # User doesn't have to be in any group
        help_text=_("Select the groups this user should belong to."),
    )

    class Meta:
        model = User
        fields = ("groups",)  # We only want to manage the 'groups' field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # If managing an existing user, pre-select their current groups
            self.initial["groups"] = self.instance.groups.values_list("pk", flat=True)
        else:
            # This form is intended for existing users, raise an error if no instance is provided
            raise ValueError("ManageUserGroupsForm must be instantiated with a user instance.")

    def save(self, commit=True):
        """
        Save the selected groups to the user's group memberships.
        """
        # The parent ModelForm save handles updating the M2M 'groups' field automatically
        # when it's included in the fields list, *if* commit=True.
        # However, we can be explicit for clarity and control.
        user = super().save(commit=False)  # Don't save the user instance yet

        if commit:
            # Update the user's groups ManyToManyField
            user.groups.set(self.cleaned_data["groups"])
            user.save()  # Save the user instance if commit is True

        return user
