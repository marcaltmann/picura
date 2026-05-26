from django.contrib import admin

from .models import Metadata, Photo


class MetadataInline(admin.TabularInline):
    model = Metadata
    extra = 0


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    inlines = [MetadataInline]
