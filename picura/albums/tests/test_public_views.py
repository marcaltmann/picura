import pytest
from django.urls import reverse
from PIL import Image

from picura.albums.models import Album
from picura.photos.models import Photo


@pytest.fixture
def make_photo(settings):
    img_dir = settings.MEDIA_ROOT / 'photos'
    img_dir.mkdir(parents=True, exist_ok=True)
    counter = [0]

    def _make(**kwargs):
        counter[0] += 1
        name = f'public_{counter[0]}.jpg'
        img = Image.new('RGB', (10, 10), color='red')
        img.save(img_dir / name, 'JPEG')
        kwargs.setdefault('title', f'Photo {counter[0]}')
        return Photo.objects.create(file=f'photos/{name}', **kwargs)

    return _make


@pytest.fixture
def make_album(db, make_photo):
    def _make(name='Album', published=True, photo_count=1):
        album = Album.objects.create(name=name)
        album.append_photos([make_photo() for _ in range(photo_count)])
        if published:
            album.publish()
            album.save()
        return album

    return _make


# --- album_list ---


@pytest.mark.django_db
def test_album_list_includes_published_album_with_photos(client, make_album):
    album = make_album()
    response = client.get(reverse('albums_album_list'))
    assert album in response.context['page_obj'].object_list


@pytest.mark.django_db
def test_album_list_excludes_draft_albums(client, make_album):
    draft = make_album(published=False)
    response = client.get(reverse('albums_album_list'))
    assert draft not in response.context['page_obj'].object_list


@pytest.mark.django_db
def test_album_list_excludes_empty_published_albums(client, make_album):
    empty = make_album(photo_count=0)
    response = client.get(reverse('albums_album_list'))
    assert empty not in response.context['page_obj'].object_list


# --- album_detail ---


@pytest.mark.django_db
def test_album_detail_returns_200_for_public_album(client, make_album):
    album = make_album()
    response = client.get(reverse('albums_album_detail', args=[album.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_detail_returns_404_for_draft_album(client, make_album):
    draft = make_album(published=False)
    response = client.get(reverse('albums_album_detail', args=[draft.pk]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_album_detail_returns_404_for_empty_published_album(client, make_album):
    empty = make_album(photo_count=0)
    response = client.get(reverse('albums_album_detail', args=[empty.pk]))
    assert response.status_code == 404


# --- album_photo_detail ---


@pytest.mark.django_db
def test_album_photo_detail_returns_200_for_public_album(client, make_album):
    album = make_album()
    photo = album.photo_at(1)
    response = client.get(reverse('albums_photo_detail', args=[album.pk, photo.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_photo_detail_returns_404_for_draft_album(client, make_album):
    draft = make_album(published=False)
    photo = draft.photo_at(1)
    response = client.get(reverse('albums_photo_detail', args=[draft.pk, photo.pk]))
    assert response.status_code == 404
