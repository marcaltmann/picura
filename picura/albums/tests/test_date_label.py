from datetime import datetime, timezone

import pytest

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def dt(year, month):
    return datetime(year, month, 1, tzinfo=timezone.utc)


def make_photo(produced_at=None):
    return Photo.objects.create(title='Photo', produced_at=produced_at)


def link(album, photo, position):
    AlbumPhoto.objects.create(album=album, photo=photo, position=position)


@pytest.fixture
def album(db):
    return Album.objects.create(name='Test Album')


@pytest.mark.django_db
def test_no_photos_returns_empty(album):
    assert album.date_label == ''


@pytest.mark.django_db
def test_all_photos_without_date_returns_empty(album):
    link(album, make_photo(produced_at=None), 1)
    assert album.date_label == ''


@pytest.mark.django_db
def test_single_photo(album):
    link(album, make_photo(dt(2026, 5)), 1)
    assert album.date_label == 'May 2026'


@pytest.mark.django_db
def test_multiple_photos_same_month(album):
    link(album, make_photo(datetime(2026, 5, 3, tzinfo=timezone.utc)), 1)
    link(album, make_photo(datetime(2026, 5, 20, tzinfo=timezone.utc)), 2)
    assert album.date_label == 'May 2026'


@pytest.mark.django_db
def test_span_within_same_year(album):
    link(album, make_photo(dt(2026, 1)), 1)
    link(album, make_photo(dt(2026, 5)), 2)
    assert album.date_label == 'Jan–May 2026'


@pytest.mark.django_db
def test_span_across_years(album):
    link(album, make_photo(dt(2024, 3)), 1)
    link(album, make_photo(dt(2026, 8)), 2)
    assert album.date_label == '2024–2026'


@pytest.mark.django_db
def test_ignores_photos_without_date(album):
    link(album, make_photo(None), 1)
    link(album, make_photo(dt(2026, 5)), 2)
    assert album.date_label == 'May 2026'


@pytest.mark.django_db
def test_date_label_uses_annotation_when_available(album):
    link(album, make_photo(dt(2025, 6)), 1)
    annotated = Album.objects.with_date_range().get(pk=album.pk)
    assert annotated.date_label == 'June 2025'
