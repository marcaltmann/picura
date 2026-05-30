import pytest

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def make_photo():
    return Photo.objects.create(title='Photo')


@pytest.fixture
def album(db):
    return Album.objects.create(name='Test Album')


@pytest.mark.django_db
def test_append_photo_to_empty_album(album):
    photo = make_photo()
    album.append_photo(photo)
    link = AlbumPhoto.objects.get(album=album, photo=photo)
    assert link.position == 1


@pytest.mark.django_db
def test_append_photo_places_at_end(album):
    p1, p2 = make_photo(), make_photo()
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    album.append_photo(p2)
    assert AlbumPhoto.objects.get(album=album, photo=p2).position == 2


@pytest.mark.django_db
def test_prepend_photo_to_empty_album(album):
    photo = make_photo()
    album.prepend_photo(photo)
    link = AlbumPhoto.objects.get(album=album, photo=photo)
    assert link.position == 1


@pytest.mark.django_db
def test_prepend_photo_shifts_existing_photos(album):
    p1, p2 = make_photo(), make_photo()
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    album.prepend_photo(p2)
    assert AlbumPhoto.objects.get(album=album, photo=p2).position == 1
    assert AlbumPhoto.objects.get(album=album, photo=p1).position == 2


@pytest.mark.django_db
def test_prepend_preserves_relative_order(album):
    photos = [make_photo() for _ in range(3)]
    for i, p in enumerate(photos, start=1):
        AlbumPhoto.objects.create(album=album, photo=p, position=i)
    new_photo = make_photo()
    album.prepend_photo(new_photo)
    positions = list(
        AlbumPhoto.objects.filter(album=album)
        .order_by('position')
        .values_list('photo_id', flat=True)
    )
    assert positions == [new_photo.pk] + [p.pk for p in photos]
