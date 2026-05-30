from django.contrib import admin

from .models import Metadata, Photo, Batch


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ['title', 'file']
    readonly_fields = ['title', 'file']
    can_delete = False


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    inlines = [PhotoInline]
    readonly_fields = ['created_at', 'updated_at']


class MetadataInline(admin.TabularInline):
    model = Metadata
    extra = 0


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    inlines = [MetadataInline]
    search_fields = ['title']
