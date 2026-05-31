import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def make_photo():
    buffer = io.BytesIO()
    Image.new('RGB', (4, 3), 'white').save(buffer, format='JPEG')
    file = SimpleUploadedFile('p.jpg', buffer.getvalue(), content_type='image/jpeg')
    return Photo.objects.create(title='Photo', file=file, width=4, height=3)


@pytest.fixture
def album_with_photos(db):
    album = Album.objects.create(name='Test Album')
    photos = [make_photo() for _ in range(3)]
    for i, photo in enumerate(photos, start=1):
        AlbumPhoto.objects.create(album=album, photo=photo, position=i)
    return album, photos


def detail_url(album, photo):
    return reverse('albums_photo_detail', args=[album.pk, photo.pk])


@pytest.mark.django_db
def test_middle_photo_has_prev_and_next(client, album_with_photos):
    album, photos = album_with_photos
    response = client.get(detail_url(album, photos[1]))
    assert response.status_code == 200
    assert response.context['prev_url'] == detail_url(album, photos[0])
    assert response.context['next_url'] == detail_url(album, photos[2])


@pytest.mark.django_db
def test_first_photo_has_no_prev(client, album_with_photos):
    album, photos = album_with_photos
    response = client.get(detail_url(album, photos[0]))
    assert response.context['prev_url'] is None
    assert response.context['next_url'] == detail_url(album, photos[1])


@pytest.mark.django_db
def test_last_photo_has_no_next(client, album_with_photos):
    album, photos = album_with_photos
    response = client.get(detail_url(album, photos[2]))
    assert response.context['prev_url'] == detail_url(album, photos[1])
    assert response.context['next_url'] is None


@pytest.mark.django_db
def test_photo_not_in_album_returns_404(client, db):
    album = Album.objects.create(name='Empty')
    other = make_photo()
    response = client.get(detail_url(album, other))
    assert response.status_code == 404
