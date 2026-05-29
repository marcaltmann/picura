from django.contrib import admin

from .models import Album, AlbumPhoto


class AlbumPhotoInline(admin.TabularInline):
    model = AlbumPhoto
    extra = 1
    autocomplete_fields = ['photo']
    fields = ['photo', 'position']


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    inlines = [AlbumPhotoInline]
