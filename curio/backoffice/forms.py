from django import forms

from curio.resources.models import Resource


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title']
