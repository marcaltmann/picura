import pytest
from django.db.models import F

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def make_photo():
    return Photo.objects.create(title='Photo')


@pytest.fixture
def album(db):
    return Album.objects.create(name='Test Album')


@pytest.mark.django_db
def test_empty_album_is_consistent(album):
    assert album.has_consistent_positions() is True


@pytest.mark.django_db
def test_contiguous_positions_are_consistent(album):
    album.append_photos([make_photo(), make_photo(), make_photo()])
    assert album.has_consistent_positions() is True


@pytest.mark.django_db
def test_gap_in_positions_is_inconsistent(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    AlbumPhoto.objects.filter(album=album, photo=p3).update(position=4)
    assert album.has_consistent_positions() is False


@pytest.mark.django_db
def test_positions_not_starting_at_one_are_inconsistent(album):
    p1, p2 = make_photo(), make_photo()
    album.append_photos([p1, p2])
    AlbumPhoto.objects.filter(album=album).update(position=F('position') + 1)
    assert album.has_consistent_positions() is False
