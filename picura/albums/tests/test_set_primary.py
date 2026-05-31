import pytest

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def make_photo():
    return Photo.objects.create(title='Photo')


@pytest.fixture
def album(db):
    return Album.objects.create(name='Test Album')


def order(album):
    return list(
        AlbumPhoto.objects.filter(album=album)
        .order_by('position')
        .values_list('photo_id', flat=True)
    )


@pytest.mark.django_db
def test_set_primary_moves_middle_photo_to_front(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    album.set_primary(p2)
    assert order(album) == [p2.pk, p1.pk, p3.pk]


@pytest.mark.django_db
def test_set_primary_moves_last_photo_to_front(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    album.set_primary(p3)
    assert order(album) == [p3.pk, p1.pk, p2.pk]


@pytest.mark.django_db
def test_set_primary_keeps_positions_contiguous(album):
    p1, p2, p3 = make_photo(), make_photo(), make_photo()
    album.append_photos([p1, p2, p3])
    album.set_primary(p3)
    positions = list(
        AlbumPhoto.objects.filter(album=album)
        .order_by('position')
        .values_list('position', flat=True)
    )
    assert positions == [1, 2, 3]


@pytest.mark.django_db
def test_set_primary_on_already_primary_is_noop(album):
    p1, p2 = make_photo(), make_photo()
    album.append_photos([p1, p2])
    album.set_primary(p1)
    assert order(album) == [p1.pk, p2.pk]


@pytest.mark.django_db
def test_set_primary_on_non_member_raises(album):
    p1 = make_photo()
    other = make_photo()
    album.append_photos(p1)
    with pytest.raises(AlbumPhoto.DoesNotExist):
        album.set_primary(other)
