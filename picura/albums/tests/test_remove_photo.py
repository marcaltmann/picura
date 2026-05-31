import pytest

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def make_photo():
    return Photo.objects.create(title='Photo')


@pytest.fixture
def album(db):
    return Album.objects.create(name='Test Album')


def positions(album):
    return list(
        AlbumPhoto.objects.filter(album=album)
        .order_by('position')
        .values_list('photo_id', 'position')
    )


@pytest.mark.django_db
def test_remove_middle_photo_compacts_positions(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    album.remove_photos(p2)
    assert positions(album) == [(p1.pk, 1), (p3.pk, 2)]


@pytest.mark.django_db
def test_remove_first_photo_compacts_positions(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    album.remove_photos(p1)
    assert positions(album) == [(p2.pk, 1), (p3.pk, 2)]


@pytest.mark.django_db
def test_remove_last_photo_leaves_remaining_intact(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    album.remove_photos(p3)
    assert positions(album) == [(p1.pk, 1), (p2.pk, 2)]


@pytest.mark.django_db
def test_remove_multiple_photos_compacts_positions(album):
    p1, p2, p3, p4 = make_photo(), make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3, p4])
    album.remove_photos([p2, p4])
    assert positions(album) == [(p1.pk, 1), (p3.pk, 2)]


@pytest.mark.django_db
def test_remove_all_photos_leaves_empty_album(album):
    p1, p2 = make_photo(), make_photo()
    album.append_photos([p1, p2])
    album.remove_photos([p1, p2])
    assert positions(album) == []


@pytest.mark.django_db
def test_remove_photo_not_in_album_is_noop(album):
    p1 = make_photo()
    other = make_photo()
    album.append_photos(p1)
    album.remove_photos(other)
    assert positions(album) == [(p1.pk, 1)]
