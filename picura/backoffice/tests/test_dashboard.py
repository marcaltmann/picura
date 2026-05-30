import pytest
from django.urls import reverse

from picura.photos.models import Photo


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
