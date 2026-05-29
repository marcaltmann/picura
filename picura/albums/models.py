from django.db import models
from django.db.models import Max, Min
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from picura.photos.models import Photo

_MISSING = object()


class AlbumQuerySet(models.QuerySet):
    def with_date_range(self):
        return self.annotate(
            min_produced_at=Min('photos__produced_at'),
            max_produced_at=Max('photos__produced_at'),
        )


class Album(models.Model):
    objects = AlbumQuerySet.as_manager()
    name = models.CharField(max_length=255, verbose_name=_('name'))
    description = models.TextField(
        blank=True, default='', verbose_name=_('description')
    )
    photos = models.ManyToManyField(
        Photo, through='AlbumPhoto', related_name='albums', verbose_name=_('photos')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('album')
        verbose_name_plural = _('albums')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('albums_album_detail', args=[self.pk])

    @property
    def date_label(self) -> str:
        min_date = self.__dict__.get('min_produced_at', _MISSING)
        if min_date is _MISSING:
            agg = self.photos.filter(produced_at__isnull=False).aggregate(
                min_date=Min('produced_at'), max_date=Max('produced_at')
            )
            min_date = agg['min_date']
            max_date = agg['max_date']
        else:
            max_date = self.__dict__['max_produced_at']

        if min_date is None:
            return ''

        if min_date.year == max_date.year:
            if min_date.month == max_date.month:
                return date_format(min_date, 'F Y')
            return f'{date_format(min_date, "M")}–{date_format(max_date, "M Y")}'
        return f'{min_date.year}–{max_date.year}'


class AlbumPhoto(models.Model):
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name='album_links',
        verbose_name=_('photo'),
    )
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='photo_links',
        verbose_name=_('album'),
    )
    position = models.PositiveIntegerField(verbose_name=_('position'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    class Meta:
        ordering = ['position']
        verbose_name = _('album photo')
        verbose_name_plural = _('album photos')

        constraints = [
            models.UniqueConstraint(
                fields=['photo', 'album'], name='unique_photo_album'
            ),
            models.UniqueConstraint(
                fields=['album', 'position'],
                name='unique_album_position',
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]

    def __str__(self):
        return f'{self.album} #{self.position}'
