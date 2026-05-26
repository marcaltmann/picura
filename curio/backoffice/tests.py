import io
from unittest.mock import patch

import pytest
from django.urls import reverse
from PIL import Image

from curio.photos.models import Photo


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
    with patch('curio.backoffice.views.upload_photos') as mock:
        response = client.post(
            reverse('backoffice_photo_upload'),
            {'files': [f]},
            format='multipart',
        )
    assert mock.called
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_photo_list')


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
