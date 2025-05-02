from django import forms

from memoria.models import Person


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ("name", "description")
