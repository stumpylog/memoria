from typing import Any
from typing import ClassVar

from django import forms
from django.contrib.auth import get_user_model

from memoria.models import UserProfile

User = get_user_model()


class UserEmailForm(forms.ModelForm):
    """Form for updating the user's email address."""

    class Meta:
        model = User
        fields: ClassVar[list] = ["email"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Add Bootstrap 5 form-control class to the email field
        self.fields["email"].widget.attrs["class"] = "form-control"


class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating the user's profile details (bio, images per page)."""

    class Meta:
        model = UserProfile
        fields: ClassVar[list] = ["bio", "images_per_page"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Add Bootstrap 5 form-control class to the fields
        self.fields["bio"].widget.attrs["class"] = "form-control"
        self.fields["images_per_page"].widget.attrs["class"] = "form-control"
