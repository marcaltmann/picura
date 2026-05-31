from django.contrib import admin

from .models import Album


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    # Photo membership and ordering are managed through the backoffice, which
    # maintains the contiguous 1..N position invariant. Editing AlbumPhoto rows
    # here would bypass that, so no inline is exposed.
    pass
