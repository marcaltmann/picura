from django import forms

from curio.resources.models import ImageResource


class ImageResourceForm(forms.ModelForm):
    class Meta:
        model = ImageResource
        fields = ['title']
