from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


def _photo_upload(instance, filename):
    return f'photos/{filename}'


class Photo(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    file = models.FileField(upload_to=_photo_upload, verbose_name=_('file'))
    media_type = models.CharField(
        max_length=100, blank=True, default='', verbose_name=_('media type')
    )
    file_size = models.PositiveIntegerField(default=0, verbose_name=_('file size'))
    description = models.TextField(
        blank=True, default='', verbose_name=_('description')
    )
    produced_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('produced at')
    )
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('width'))
    height = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_('height')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    thumbnail_300 = ImageSpecField(
        source='file',
        processors=[ResizeToFit(300, 300)],
        format='WEBP',
        options={'quality': 60},
    )
    thumbnail_500 = ImageSpecField(
        source='file',
        processors=[ResizeToFit(500, 500)],
        format='WEBP',
        options={'quality': 60},
    )
    thumbnail_800 = ImageSpecField(
        source='file',
        processors=[ResizeToFit(800, 800)],
        format='WEBP',
        options={'quality': 60},
    )
    detail_1000 = ImageSpecField(
        source='file',
        processors=[ResizeToFit(1000, 1000)],
        format='WEBP',
        options={'quality': 80},
    )
    thumbnail_2000 = ImageSpecField(
        source='file',
        processors=[ResizeToFit(2000, 2000)],
        format='WEBP',
        options={'quality': 80},
    )
    thumbnail_3000 = ImageSpecField(
        source='file',
        processors=[ResizeToFit(3000, 3000)],
        format='WEBP',
        options={'quality': 80},
    )

    class Meta:
        verbose_name = _('photo')
        verbose_name_plural = _('photos')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('photos_photo_detail', args=[self.pk])


class Metadata(models.Model):
    class Type(models.TextChoices):
        EXIF = 'exif', _('EXIF')
        DUBLIN_CORE = 'dc', _('Dublin Core')
        CUSTOM = 'custom', _('Custom')

    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name='metadata',
        verbose_name=_('photo'),
    )
    type = models.CharField(max_length=16, choices=Type.choices, verbose_name=_('type'))
    data = models.JSONField(verbose_name=_('data'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        verbose_name = _('metadata')
        verbose_name_plural = _('metadata')

    def __str__(self):
        return f'{self.get_type_display()} – {self.photo}'


@receiver(post_delete, sender=Photo)
def delete_photo_file(sender, instance, **kwargs):
    instance.file.delete(save=False)
