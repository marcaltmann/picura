import math
from fractions import Fraction

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.formats import date_format as _date_format
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


def _photo_upload(instance, filename):
    return f'photos/{filename}'


class Batch(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        verbose_name = _('batch')
        verbose_name_plural = _('batches')

    def __str__(self):
        return str(self.created_at)


class Photo(models.Model):
    batch = models.ForeignKey(
        Batch,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='photos',
        verbose_name=_('batch'),
    )
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
    detail_2000 = ImageSpecField(
        source='file',
        processors=[ResizeToFit(2000, 2000)],
        format='WEBP',
        options={'quality': 80},
    )
    detail_3000 = ImageSpecField(
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

    _DISPLAY_AREA = 720 * 480

    @property
    def aspect_ratio(self):
        if self.width is None or self.height is None:
            return None
        return self.width / self.height

    @property
    def display_width(self):
        if self.aspect_ratio is None:
            return None
        return round(math.sqrt(self._DISPLAY_AREA * self.aspect_ratio))

    @property
    def date_display(self):
        if self.produced_at is None:
            return ''
        return _date_format(self.produced_at, 'DATE_FORMAT')

    @property
    def place(self):
        return ''

    @property
    def map_tile_url(self):
        try:
            lat = self.exif.latitude
            lon = self.exif.longitude
        except ObjectDoesNotExist:
            return None
        if lat is None or lon is None:
            return None
        zoom = 12
        n = 2**zoom
        x = int((lon + 180) / 360 * n)
        y = int(
            (
                1
                - math.log(
                    math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))
                )
                / math.pi
            )
            / 2
            * n
        )
        return f'https://tile.openstreetmap.org/{zoom}/{x}/{y}.png'


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


class PhotoExif(models.Model):
    photo = models.OneToOneField(
        Photo,
        on_delete=models.CASCADE,
        related_name='exif',
        verbose_name=_('photo'),
    )
    camera_make = models.CharField(
        max_length=255, blank=True, default='', verbose_name=_('camera make')
    )
    camera_model = models.CharField(
        max_length=255, blank=True, default='', verbose_name=_('camera model')
    )
    lens = models.CharField(
        max_length=255, blank=True, default='', verbose_name=_('lens')
    )
    aperture = models.FloatField(null=True, blank=True, verbose_name=_('aperture'))
    exposure_time = models.FloatField(
        null=True, blank=True, verbose_name=_('exposure time')
    )
    focal_length = models.FloatField(
        null=True, blank=True, verbose_name=_('focal length')
    )
    iso = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('ISO'))
    latitude = models.FloatField(null=True, blank=True, verbose_name=_('latitude'))
    longitude = models.FloatField(null=True, blank=True, verbose_name=_('longitude'))
    raw = models.JSONField(default=dict, verbose_name=_('raw'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        verbose_name = _('EXIF')
        verbose_name_plural = _('EXIF')

    def __str__(self):
        return f'EXIF – {self.photo}'

    @property
    def shutter_speed(self) -> str | None:
        if self.exposure_time is None:
            return None
        frac = Fraction(self.exposure_time).limit_denominator(100000)
        if frac.denominator == 1:
            return str(frac.numerator)
        return f'{frac.numerator}/{frac.denominator}'


@receiver(post_delete, sender=Photo)
def delete_photo_file(sender, instance, **kwargs):
    instance.file.delete(save=False)
