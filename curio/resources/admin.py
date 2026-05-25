from django.contrib import admin

from .models import Metadata, Resource


class MetadataInline(admin.TabularInline):
    model = Metadata
    extra = 0


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    inlines = [MetadataInline]
