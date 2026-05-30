import pytest

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def make_photo():
    return Photo.objects.create(title='Photo')


@pytest.fixture
def album(db):
    return Album.objects.create(name='Test Album')


# --- append_photos ---


@pytest.mark.django_db
def test_append_single_photo_to_empty_album(album):
    photo = make_photo()
    result = album.append_photos(photo)
    assert len(result) == 1
    assert AlbumPhoto.objects.get(album=album, photo=photo).position == 1


@pytest.mark.django_db
def test_append_single_photo_places_at_end(album):
    p1, p2 = make_photo(), make_photo()
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    album.append_photos(p2)
    assert AlbumPhoto.objects.get(album=album, photo=p2).position == 2


@pytest.mark.django_db
def test_append_multiple_photos(album):
    p1 = make_photo()
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    p2, p3 = make_photo(), make_photo()
    result = album.append_photos([p2, p3])
    assert len(result) == 2
    assert AlbumPhoto.objects.get(album=album, photo=p2).position == 2
    assert AlbumPhoto.objects.get(album=album, photo=p3).position == 3


@pytest.mark.django_db
def test_append_photos_returns_list(album):
    photo = make_photo()
    result = album.append_photos(photo)
    assert isinstance(result, list)


# --- prepend_photos ---


@pytest.mark.django_db
def test_prepend_single_photo_to_empty_album(album):
    photo = make_photo()
    result = album.prepend_photos(photo)
    assert len(result) == 1
    assert AlbumPhoto.objects.get(album=album, photo=photo).position == 1


@pytest.mark.django_db
def test_prepend_single_photo_shifts_existing(album):
    p1, p2 = make_photo(), make_photo()
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    album.prepend_photos(p2)
    assert AlbumPhoto.objects.get(album=album, photo=p2).position == 1
    assert AlbumPhoto.objects.get(album=album, photo=p1).position == 2


@pytest.mark.django_db
def test_prepend_multiple_photos(album):
    p1 = make_photo()
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    p2, p3 = make_photo(), make_photo()
    result = album.prepend_photos([p2, p3])
    assert len(result) == 2
    assert AlbumPhoto.objects.get(album=album, photo=p2).position == 1
    assert AlbumPhoto.objects.get(album=album, photo=p3).position == 2
    assert AlbumPhoto.objects.get(album=album, photo=p1).position == 3


@pytest.mark.django_db
def test_prepend_photos_preserves_relative_order(album):
    photos = [make_photo() for _ in range(3)]
    for i, p in enumerate(photos, start=1):
        AlbumPhoto.objects.create(album=album, photo=p, position=i)
    new_photos = [make_photo(), make_photo()]
    album.prepend_photos(new_photos)
    positions = list(
        AlbumPhoto.objects.filter(album=album)
        .order_by('position')
        .values_list('photo_id', flat=True)
    )
    assert positions == [p.pk for p in new_photos] + [p.pk for p in photos]


@pytest.mark.django_db
def test_prepend_photos_returns_list(album):
    photo = make_photo()
    result = album.prepend_photos(photo)
    assert isinstance(result, list)
