import pytest
from django.test import Client
from django.urls import reverse

from picura.albums.models import Album

# Backoffice URLs reachable with a plain GET and no existing object required.
PROTECTED_URLS = [
    'backoffice_dashboard',
    'backoffice_batch_list',
    'backoffice_photo_list',
    'backoffice_photo_upload',
    'backoffice_album_list',
    'backoffice_album_create',
]


@pytest.mark.django_db
@pytest.mark.parametrize('url_name', PROTECTED_URLS)
def test_anonymous_is_redirected_to_login(url_name):
    response = Client().get(reverse(url_name))
    assert response.status_code == 302
    assert reverse('account_login') in response['Location']


@pytest.mark.django_db
@pytest.mark.parametrize('url_name', PROTECTED_URLS)
def test_non_staff_is_forbidden(url_name, non_staff_user):
    client = Client()
    client.force_login(non_staff_user)
    response = client.get(reverse(url_name))
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('url_name', PROTECTED_URLS)
def test_staff_is_allowed(url_name, staff_user):
    client = Client()
    client.force_login(staff_user)
    response = client.get(reverse(url_name))
    assert response.status_code == 200


@pytest.mark.django_db
def test_anonymous_cannot_delete_album():
    album = Album.objects.create(name='Protected')
    response = Client().post(reverse('backoffice_album_delete', args=[album.pk]))
    assert response.status_code == 302
    assert reverse('account_login') in response['Location']
    assert Album.objects.filter(pk=album.pk).exists()
