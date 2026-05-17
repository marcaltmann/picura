from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


def _media_file_upload(instance, filename):
    folders = {
        Resource.Type.IMAGE: 'images',
        Resource.Type.AUDIO: 'audio',
        Resource.Type.VIDEO: 'videos',
        Resource.Type.DOCUMENT: 'documents',
    }
    resource_type = instance.resource.resource_type if instance.resource_id else None
    return f'{folders.get(resource_type, "media")}/{filename}'


class Resource(models.Model):
    class Type(models.TextChoices):
        IMAGE = 'image', _('Image')
        AUDIO = 'audio', _('Audio')
        VIDEO = 'video', _('Video')
        DOCUMENT = 'document', _('Document')

    resource_type = models.CharField(
        max_length=16, choices=Type.choices, verbose_name=_('type')
    )
    title = models.CharField(max_length=255, verbose_name=_('title'))
    description = models.TextField(
        blank=True, default='', verbose_name=_('description')
    )
    produced_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('produced at')
    )
    poster = models.ImageField(
        upload_to='posters/', null=True, blank=True, verbose_name=_('poster')
    )
    poster_thumbnail = ImageSpecField(
        source='poster',
        processors=[ResizeToFit(300, 300)],
        format='JPEG',
        options={'quality': 80},
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    @property
    def primary_file(self):
        return next(iter(self.files.all()), None)

    @property
    def thumbnail(self):
        if self.resource_type == self.Type.IMAGE:
            pf = self.primary_file
            if pf:
                return pf.file_thumbnail
        return self.poster_thumbnail

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('resource_detail', args=[self.pk])

    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')

    def __str__(self):
        return self.title


class MediaFile(models.Model):
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name=_('resource'),
    )
    file = models.FileField(upload_to=_media_file_upload, verbose_name=_('file'))
    media_type = models.CharField(
        max_length=100, blank=True, default='', verbose_name=_('media type')
    )
    file_size = models.PositiveIntegerField(default=0, verbose_name=_('file size'))
    role = models.CharField(
        max_length=50, blank=True, default='', verbose_name=_('role')
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_('order'))
    # Audio & Video
    duration = models.DurationField(null=True, blank=True, verbose_name=_('duration'))
    # Image & Video
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('width'))
    height = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('height')
    )
    # Document
    page_count = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('page count')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    file_thumbnail = ImageSpecField(
        source='file',
        processors=[ResizeToFit(300, 300)],
        format='JPEG',
        options={'quality': 80},
    )

    class Meta:
        verbose_name = _('media file')
        verbose_name_plural = _('media files')
        ordering = ['order']

    def __str__(self):
        return f'{self.resource} ({self.media_type or self.file.name})'


class Metadata(models.Model):
    class Type(models.TextChoices):
        EXIF = 'exif', _('EXIF')
        DUBLIN_CORE = 'dc', _('Dublin Core')
        CUSTOM = 'custom', _('Custom')

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='metadata',
        verbose_name=_('resource'),
    )
    type = models.CharField(max_length=16, choices=Type.choices, verbose_name=_('type'))
    data = models.JSONField(verbose_name=_('data'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        verbose_name = _('metadata')
        verbose_name_plural = _('metadata')

    def __str__(self):
        return f'{self.get_type_display()} – {self.resource}'


@receiver(post_delete, sender=Resource)
def delete_resource_poster(sender, instance, **kwargs):
    if instance.poster:
        instance.poster.delete(save=False)


@receiver(post_delete, sender=MediaFile)
def delete_media_file(sender, instance, **kwargs):
    instance.file.delete(save=False)
