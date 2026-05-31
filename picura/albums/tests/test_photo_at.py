import pytest

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


@pytest.fixture
def album_with_photos(db):
    album = Album.objects.create(name='Test Album')
    photos = [Photo.objects.create(title=f'Photo {i}') for i in range(3)]
    for i, photo in enumerate(photos, start=1):
        AlbumPhoto.objects.create(album=album, photo=photo, position=i)
    return album, photos


@pytest.mark.django_db
def test_photo_at_returns_photo_at_position(album_with_photos):
    album, photos = album_with_photos
    assert album.photo_at(1) == photos[0]
    assert album.photo_at(2) == photos[1]
    assert album.photo_at(3) == photos[2]


@pytest.mark.django_db
def test_photo_at_missing_position_raises(album_with_photos):
    album, _ = album_with_photos
    with pytest.raises(Photo.DoesNotExist):
        album.photo_at(4)
