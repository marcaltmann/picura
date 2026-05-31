import pytest
from django.urls import reverse

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


@pytest.fixture
def album_with_photos(db):
    album = Album.objects.create(name='Test Album')
    photos = [Photo.objects.create(title=f'Photo {i}') for i in range(3)]
    for i, photo in enumerate(photos, start=1):
        AlbumPhoto.objects.create(album=album, photo=photo, position=i)
    return album, photos


# --- Album.neighbour_photo_ids ---


@pytest.mark.django_db
def test_middle_photo_has_both_neighbours(album_with_photos):
    album, photos = album_with_photos
    assert album.neighbour_photo_ids(2) == (photos[0].pk, photos[2].pk)


@pytest.mark.django_db
def test_first_photo_has_no_previous(album_with_photos):
    album, photos = album_with_photos
    assert album.neighbour_photo_ids(1) == (None, photos[1].pk)


@pytest.mark.django_db
def test_last_photo_has_no_next(album_with_photos):
    album, photos = album_with_photos
    assert album.neighbour_photo_ids(3) == (photos[1].pk, None)


# --- album_photo_detail view ---


@pytest.mark.django_db
def test_photo_not_in_album_returns_404(client, db):
    album = Album.objects.create(name='Empty')
    other = Photo.objects.create(title='Other')
    url = reverse('albums_photo_detail', args=[album.pk, other.pk])
    assert client.get(url).status_code == 404
