import io
from unittest.mock import patch

import pytest
from django.urls import reverse
from PIL import Image

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Batch, Photo


@pytest.fixture
def photo(settings):
    img_dir = settings.MEDIA_ROOT / 'photos'
    img_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', (10, 10), color='red')
    img.save(img_dir / 'test.jpg', 'JPEG')
    return Photo.objects.create(title='Test Photo', file='photos/test.jpg')


@pytest.mark.django_db
def test_dashboard_returns_200(client):
    response = client.get(reverse('backoffice_dashboard'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_context_photo_count(client):
    Photo.objects.create(title='A', file='photos/a.jpg', file_size=100)
    Photo.objects.create(title='B', file='photos/b.jpg', file_size=200)
    response = client.get(reverse('backoffice_dashboard'))
    assert response.context['photo_count'] == 2


@pytest.mark.django_db
def test_dashboard_context_total_file_size(client):
    Photo.objects.create(title='A', file='photos/a.jpg', file_size=1000)
    Photo.objects.create(title='B', file='photos/b.jpg', file_size=2000)
    response = client.get(reverse('backoffice_dashboard'))
    assert response.context['total_file_size'] == 3000


@pytest.mark.django_db
def test_dashboard_context_empty_db(client):
    response = client.get(reverse('backoffice_dashboard'))
    assert response.context['photo_count'] == 0
    assert response.context['total_file_size'] == 0


@pytest.mark.django_db
def test_photo_list_returns_200(client):
    response = client.get(reverse('backoffice_photo_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_photo_list_shows_photos(client, photo):
    response = client.get(reverse('backoffice_photo_list'))
    assert b'Test Photo' in response.content


@pytest.mark.django_db
def test_photo_upload_get_returns_200(client):
    response = client.get(reverse('backoffice_photo_upload'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_photo_detail_returns_200(client, photo):
    response = client.get(reverse('backoffice_photo_detail', args=[photo.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_photo_detail_shows_title(client, photo):
    response = client.get(reverse('backoffice_photo_detail', args=[photo.pk]))
    assert b'Test Photo' in response.content


@pytest.mark.django_db
def test_photo_detail_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_photo_detail', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_photo_upload_post_calls_use_case_and_redirects(client):
    f = io.BytesIO(b'image data')
    f.name = 'my-photo.jpg'
    batch = Batch.objects.create()
    with patch('picura.backoffice.views.upload_photos', return_value=batch) as mock:
        response = client.post(
            reverse('backoffice_photo_upload'),
            {'files': [f]},
            format='multipart',
        )
    assert mock.called
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_batch_detail', args=[batch.pk])


@pytest.mark.django_db
def test_photo_detail_post_updates_title_and_redirects(client):
    p = Photo.objects.create(title='Old Title', file='photos/test.jpg')
    response = client.post(
        reverse('backoffice_photo_detail', args=[p.pk]),
        {'title': 'New Title'},
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_photo_detail', args=[p.pk])
    p.refresh_from_db()
    assert p.title == 'New Title'


@pytest.mark.django_db
def test_photo_detail_post_invalid_rerenders_form(client, photo):
    response = client.post(
        reverse('backoffice_photo_detail', args=[photo.pk]),
        {'title': ''},
    )
    assert response.status_code == 200
    photo.refresh_from_db()
    assert photo.title == 'Test Photo'


@pytest.mark.django_db
def test_photo_delete_get_returns_200(client):
    p = Photo.objects.create(title='Delete Me', file='photos/test.jpg')
    response = client.get(reverse('backoffice_photo_delete', args=[p.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_photo_delete_get_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_photo_delete', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_photo_delete_post_deletes_and_redirects(client):
    p = Photo.objects.create(title='Delete Me', file='photos/test.jpg')
    response = client.post(reverse('backoffice_photo_delete', args=[p.pk]))
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_photo_list')
    assert not Photo.objects.filter(pk=p.pk).exists()


@pytest.mark.django_db
def test_photo_bulk_delete_post_deletes_and_redirects(client):
    p1 = Photo.objects.create(title='A', file='photos/a.jpg')
    p2 = Photo.objects.create(title='B', file='photos/b.jpg')
    p3 = Photo.objects.create(title='C', file='photos/c.jpg')
    response = client.post(
        reverse('backoffice_photo_bulk_delete'),
        {'photo_ids': [p1.pk, p2.pk]},
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_photo_list')
    assert not Photo.objects.filter(pk__in=[p1.pk, p2.pk]).exists()
    assert Photo.objects.filter(pk=p3.pk).exists()


@pytest.mark.django_db
def test_photo_bulk_delete_post_with_no_ids_redirects(client):
    Photo.objects.create(title='A', file='photos/a.jpg')
    response = client.post(reverse('backoffice_photo_bulk_delete'), {})
    assert response.status_code == 302
    assert Photo.objects.count() == 1


@pytest.mark.django_db
def test_photo_bulk_delete_get_redirects(client):
    response = client.get(reverse('backoffice_photo_bulk_delete'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_batch_list_returns_200(client):
    response = client.get(reverse('backoffice_batch_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_batch_list_context_contains_batches(client):
    batch = Batch.objects.create()
    response = client.get(reverse('backoffice_batch_list'))
    assert batch in response.context['batch_list']


@pytest.fixture
def make_photo(settings):
    img_dir = settings.MEDIA_ROOT / 'photos'
    img_dir.mkdir(parents=True, exist_ok=True)
    counter = [0]

    def _make(batch=None, **kwargs):
        counter[0] += 1
        name = f'test_{counter[0]}.jpg'
        img = Image.new('RGB', (10, 10), color='red')
        img.save(img_dir / name, 'JPEG')
        return Photo.objects.create(
            title=kwargs.get('title', f'Photo {counter[0]}'),
            file=f'photos/{name}',
            batch=batch,
        )

    return _make


@pytest.mark.django_db
def test_batch_list_annotates_photo_count(client, make_photo):
    batch = Batch.objects.create()
    make_photo(batch=batch)
    make_photo(batch=batch)
    response = client.get(reverse('backoffice_batch_list'))
    assert response.context['batch_list'][0].photo_count == 2


@pytest.mark.django_db
def test_batch_list_annotates_assigned_count_zero_when_unassigned(client, make_photo):
    batch = Batch.objects.create()
    make_photo(batch=batch)
    response = client.get(reverse('backoffice_batch_list'))
    assert response.context['batch_list'][0].assigned_count == 0


@pytest.mark.django_db
def test_batch_list_annotates_assigned_count_when_some_assigned(client, make_photo):
    batch = Batch.objects.create()
    p1 = make_photo(batch=batch)
    make_photo(batch=batch)
    album = Album.objects.create(name='Test Album')
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    response = client.get(reverse('backoffice_batch_list'))
    assert response.context['batch_list'][0].assigned_count == 1


@pytest.mark.django_db
def test_batch_detail_returns_200(client):
    batch = Batch.objects.create()
    response = client.get(reverse('backoffice_batch_detail', args=[batch.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_batch_detail_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_batch_detail', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_batch_detail_context_contains_batch(client):
    batch = Batch.objects.create()
    response = client.get(reverse('backoffice_batch_detail', args=[batch.pk]))
    assert response.context['batch'] == batch


# Album views


@pytest.mark.django_db
def test_album_list_returns_200(client):
    response = client.get(reverse('backoffice_album_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_list_context_contains_albums(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_list'))
    assert album in response.context['album_list']


@pytest.mark.django_db
def test_album_list_shows_album_name(client):
    Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_list'))
    assert b'Summer 2024' in response.content


@pytest.mark.django_db
def test_album_create_get_returns_200(client):
    response = client.get(reverse('backoffice_album_create'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_create_post_creates_album_and_redirects(client):
    response = client.post(reverse('backoffice_album_create'), {'name': 'New Album'})
    assert response.status_code == 302
    album = Album.objects.get(name='New Album')
    assert response['Location'] == reverse('backoffice_album_detail', args=[album.pk])


@pytest.mark.django_db
def test_album_create_post_invalid_rerenders(client):
    response = client.post(reverse('backoffice_album_create'), {'name': ''})
    assert response.status_code == 200
    assert Album.objects.count() == 0


@pytest.mark.django_db
def test_album_detail_returns_200(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_detail_context_contains_album(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert response.context['album'] == album


@pytest.mark.django_db
def test_album_detail_shows_album_name(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert b'Summer 2024' in response.content


@pytest.mark.django_db
def test_album_detail_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_album_detail', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_album_detail_post_updates_name_and_redirects(client):
    album = Album.objects.create(name='Old Name')
    response = client.post(
        reverse('backoffice_album_detail', args=[album.pk]),
        {'name': 'New Name'},
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_album_detail', args=[album.pk])
    album.refresh_from_db()
    assert album.name == 'New Name'


@pytest.mark.django_db
def test_album_detail_post_invalid_rerenders(client):
    album = Album.objects.create(name='Old Name')
    response = client.post(
        reverse('backoffice_album_detail', args=[album.pk]),
        {'name': ''},
    )
    assert response.status_code == 200
    album.refresh_from_db()
    assert album.name == 'Old Name'


@pytest.mark.django_db
def test_album_delete_get_returns_200(client):
    album = Album.objects.create(name='To Delete')
    response = client.get(reverse('backoffice_album_delete', args=[album.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_delete_get_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_album_delete', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_album_delete_post_deletes_and_redirects(client):
    album = Album.objects.create(name='To Delete')
    response = client.post(reverse('backoffice_album_delete', args=[album.pk]))
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_album_list')
    assert not Album.objects.filter(pk=album.pk).exists()
