import io
from unittest.mock import patch

import pytest
from django.urls import reverse
from PIL import Image

from curio.resources.models import MediaFile, Resource


@pytest.fixture
def image_resource(settings):
    img_dir = settings.MEDIA_ROOT / 'images'
    img_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', (10, 10), color='red')
    img.save(img_dir / 'test.jpg', 'JPEG')
    resource = Resource.objects.create(
        resource_type=Resource.Type.IMAGE, title='Test Image'
    )
    MediaFile.objects.create(resource=resource, file='images/test.jpg')
    return resource


@pytest.mark.django_db
def test_dashboard_returns_200(client):
    response = client.get(reverse('backoffice_dashboard'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_audio_list_returns_200(client):
    response = client.get(reverse('backoffice_audio_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_audio_list_shows_resources(client):
    Resource.objects.create(resource_type=Resource.Type.AUDIO, title='Test Podcast')
    response = client.get(reverse('backoffice_audio_list'))
    assert b'Test Podcast' in response.content


@pytest.mark.django_db
def test_audio_upload_get_returns_200(client):
    response = client.get(reverse('backoffice_audio_upload'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_audio_detail_returns_200(client):
    audio = Resource.objects.create(resource_type=Resource.Type.AUDIO, title='Detail Test')
    MediaFile.objects.create(resource=audio, file='audio/test.mp3')
    response = client.get(reverse('backoffice_audio_detail', args=[audio.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_audio_detail_shows_title(client):
    audio = Resource.objects.create(resource_type=Resource.Type.AUDIO, title='Detail Test')
    MediaFile.objects.create(resource=audio, file='audio/test.mp3')
    response = client.get(reverse('backoffice_audio_detail', args=[audio.pk]))
    assert b'Detail Test' in response.content


@pytest.mark.django_db
def test_audio_detail_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_audio_detail', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_audio_upload_post_calls_use_case_and_redirects(client):
    f = io.BytesIO(b'audio data')
    f.name = 'my-podcast.mp3'
    with patch('curio.backoffice.views.upload_audio_files') as mock:
        response = client.post(
            reverse('backoffice_audio_upload'),
            {'files': [f]},
            format='multipart',
        )
    assert mock.called
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_audio_list')


@pytest.mark.django_db
def test_audio_delete_get_returns_200(client):
    audio = Resource.objects.create(resource_type=Resource.Type.AUDIO, title='Delete Me')
    response = client.get(reverse('backoffice_audio_delete', args=[audio.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_audio_delete_get_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_audio_delete', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_audio_delete_post_deletes_and_redirects(client):
    audio = Resource.objects.create(resource_type=Resource.Type.AUDIO, title='Delete Me')
    response = client.post(reverse('backoffice_audio_delete', args=[audio.pk]))
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_audio_list')
    assert not Resource.objects.filter(pk=audio.pk).exists()


@pytest.mark.django_db
def test_image_detail_post_updates_title_and_redirects(client):
    image = Resource.objects.create(resource_type=Resource.Type.IMAGE, title='Old Title')
    MediaFile.objects.create(resource=image, file='images/test.jpg')
    response = client.post(
        reverse('backoffice_image_detail', args=[image.pk]),
        {'title': 'New Title'},
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_image_detail', args=[image.pk])
    image.refresh_from_db()
    assert image.title == 'New Title'


@pytest.mark.django_db
def test_image_detail_post_invalid_rerenders_form(client, image_resource):
    response = client.post(
        reverse('backoffice_image_detail', args=[image_resource.pk]),
        {'title': ''},
    )
    assert response.status_code == 200
    image_resource.refresh_from_db()
    assert image_resource.title == 'Test Image'


@pytest.mark.django_db
def test_image_delete_get_returns_200(client):
    image = Resource.objects.create(resource_type=Resource.Type.IMAGE, title='Delete Me')
    MediaFile.objects.create(resource=image, file='images/test.jpg')
    response = client.get(reverse('backoffice_image_delete', args=[image.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_image_delete_post_deletes_and_redirects(client):
    image = Resource.objects.create(resource_type=Resource.Type.IMAGE, title='Delete Me')
    response = client.post(reverse('backoffice_image_delete', args=[image.pk]))
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_image_list')
    assert not Resource.objects.filter(pk=image.pk).exists()


@pytest.mark.django_db
def test_video_delete_get_returns_200(client):
    video = Resource.objects.create(resource_type=Resource.Type.VIDEO, title='Delete Me')
    response = client.get(reverse('backoffice_video_delete', args=[video.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_video_delete_post_deletes_and_redirects(client):
    video = Resource.objects.create(resource_type=Resource.Type.VIDEO, title='Delete Me')
    response = client.post(reverse('backoffice_video_delete', args=[video.pk]))
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_video_list')
    assert not Resource.objects.filter(pk=video.pk).exists()
