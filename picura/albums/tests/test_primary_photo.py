import pytest

from picura.albums.models import Album
from picura.photos.models import Photo


def make_photo():
    return Photo.objects.create(title='Photo')


@pytest.fixture
def album(db):
    return Album.objects.create(name='Test Album')


@pytest.mark.django_db
def test_primary_photo_is_position_one(album):
    p1, p2 = make_photo(), make_photo()
    album.append_photos([p1, p2])
    assert album.primary_photo == p1


@pytest.mark.django_db
def test_primary_photo_reflects_set_primary(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    album.set_primary(p3)
    assert album.primary_photo == p3


@pytest.mark.django_db
def test_primary_photo_is_none_for_empty_album(album):
    assert album.primary_photo is None
