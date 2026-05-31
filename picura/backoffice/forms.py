from django import forms

from picura.albums.models import Album
from picura.photos.models import Photo


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['title']


class AlbumCreateForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['name', 'description']


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['name', 'description', 'status']
