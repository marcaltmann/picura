from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


def _resource_file_upload(instance, filename):
    folders = {
        Resource.Type.IMAGE: 'images',
        Resource.Type.AUDIO: 'audio',
        Resource.Type.VIDEO: 'videos',
    }
    return f'{folders.get(instance.resource_type, "resources")}/{filename}'


class Resource(models.Model):
    class Type(models.TextChoices):
        IMAGE = 'image', _('Image')
        AUDIO = 'audio', _('Audio')
        VIDEO = 'video', _('Video')

    resource_type = models.CharField(
        max_length=16, choices=Type.choices, verbose_name=_('type')
    )
    title = models.CharField(max_length=255, verbose_name=_('title'))
    file = models.FileField(upload_to=_resource_file_upload, verbose_name=_('file'))
    media_type = models.CharField(
        max_length=100, blank=True, default='', verbose_name=_('media type')
    )
    file_size = models.PositiveIntegerField(default=0, verbose_name=_('file size'))
    produced_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('produced at')
    )
    # Audio & Video
    poster = models.ImageField(
        upload_to='posters/', null=True, blank=True, verbose_name=_('poster')
    )
    duration = models.DurationField(null=True, blank=True, verbose_name=_('duration'))
    # Image & Video
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('width'))
    height = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('height')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    file_thumbnail = ImageSpecField(
        source='file',
        processors=[ResizeToFit(300, 300)],
        format='JPEG',
        options={'quality': 80},
    )
    poster_thumbnail = ImageSpecField(
        source='poster',
        processors=[ResizeToFit(300, 300)],
        format='JPEG',
        options={'quality': 80},
    )

    @property
    def thumbnail(self):
        if self.resource_type == self.Type.IMAGE:
            return self.file_thumbnail
        return self.poster_thumbnail

    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')

    def __str__(self):
        return self.title


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
def delete_resource_files(sender, instance, **kwargs):
    instance.file.delete(save=False)
    if instance.poster:
        instance.poster.delete(save=False)
