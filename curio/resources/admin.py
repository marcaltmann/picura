from django.contrib import admin

from .models import MediaFile, Metadata, Resource


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 0


class MetadataInline(admin.TabularInline):
    model = Metadata
    extra = 0


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    inlines = [MediaFileInline, MetadataInline]
