from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class Resource(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    file_size = models.PositiveIntegerField(default=0, verbose_name=_('file size'))
    produced_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('produced at')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')

    def __str__(self):
        return self.title


class AudioResource(Resource):
    file = models.FileField(upload_to='audio/', verbose_name=_('file'))
    duration = models.DurationField(null=True, blank=True, verbose_name=_('duration'))

    class Meta:
        verbose_name = _('audio resource')
        verbose_name_plural = _('audio resources')


class ImageResource(Resource):
    file = models.ImageField(upload_to='images/', verbose_name=_('file'))
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('width'))
    height = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('height')
    )

    class Meta:
        verbose_name = _('image resource')
        verbose_name_plural = _('image resources')


class VideoResource(Resource):
    file = models.FileField(upload_to='videos/', verbose_name=_('file'))
    poster = models.ImageField(
        upload_to='video_posters/', null=True, blank=True, verbose_name=_('poster')
    )
    duration = models.DurationField(null=True, blank=True, verbose_name=_('duration'))
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('width'))
    height = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('height')
    )

    class Meta:
        verbose_name = _('video resource')
        verbose_name_plural = _('video resources')


@receiver(post_delete, sender=AudioResource)
def delete_audio_file(sender, instance, **kwargs):
    instance.file.delete(save=False)


@receiver(post_delete, sender=ImageResource)
def delete_image_file(sender, instance, **kwargs):
    instance.file.delete(save=False)


@receiver(post_delete, sender=VideoResource)
def delete_video_files(sender, instance, **kwargs):
    instance.file.delete(save=False)
    if instance.poster:
        instance.poster.delete(save=False)


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
