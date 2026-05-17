from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .models import MediaFile, Metadata, Resource
from .use_cases import upload_audio_files, upload_image_files, upload_video_files


@pytest.mark.django_db
def test_metadata_can_be_attached_to_resource():
    resource = Resource.objects.create(resource_type=Resource.Type.IMAGE, title='Photo')
    meta = Metadata.objects.create(
        resource=resource,
        type=Metadata.Type.EXIF,
        data={'Make': 'Canon', 'Model': 'EOS R5'},
    )
    assert resource.metadata.count() == 1
    assert resource.metadata.first() == meta


@pytest.mark.django_db
def test_metadata_accessible_via_resource():
    resource = Resource.objects.create(
        resource_type=Resource.Type.AUDIO, title='Podcast'
    )
    Metadata.objects.create(
        resource=resource,
        type=Metadata.Type.DUBLIN_CORE,
        data={'creator': 'Alice', 'rights': 'CC BY 4.0'},
    )
    assert resource.metadata.count() == 1


@pytest.mark.django_db
def test_metadata_deleted_with_resource():
    resource = Resource.objects.create(resource_type=Resource.Type.VIDEO, title='Clip')
    Metadata.objects.create(
        resource=resource, type=Metadata.Type.CUSTOM, data={'foo': 'bar'}
    )
    resource.delete()
    assert Metadata.objects.count() == 0


@pytest.mark.django_db
def test_multiple_metadata_types_per_resource():
    resource = Resource.objects.create(resource_type=Resource.Type.IMAGE, title='Photo')
    Metadata.objects.create(
        resource=resource, type=Metadata.Type.EXIF, data={'ISO': 400}
    )
    Metadata.objects.create(
        resource=resource, type=Metadata.Type.DUBLIN_CORE, data={'creator': 'Bob'}
    )
    assert resource.metadata.count() == 2
    types = set(resource.metadata.values_list('type', flat=True))
    assert types == {Metadata.Type.EXIF, Metadata.Type.DUBLIN_CORE}


@pytest.mark.django_db
def test_deleting_media_file_deletes_file():
    resource = Resource.objects.create(
        resource_type=Resource.Type.AUDIO, title='Podcast'
    )
    media_file = MediaFile.objects.create(
        resource=resource,
        file=SimpleUploadedFile('ep.mp3', b'audio data'),
    )
    name = media_file.file.name
    media_file.delete()
    assert not media_file.file.storage.exists(name)


@pytest.mark.django_db
def test_deleting_resource_cascades_to_media_files():
    resource = Resource.objects.create(
        resource_type=Resource.Type.AUDIO, title='Podcast'
    )
    media_file = MediaFile.objects.create(
        resource=resource,
        file=SimpleUploadedFile('ep.mp3', b'audio data'),
    )
    name = media_file.file.name
    resource.delete()
    assert not media_file.file.storage.exists(name)


@pytest.mark.django_db
def test_deleting_resource_with_poster_deletes_poster():
    resource = Resource.objects.create(
        resource_type=Resource.Type.VIDEO,
        title='Clip',
        poster=SimpleUploadedFile('poster.jpg', b'image data'),
    )
    MediaFile.objects.create(
        resource=resource,
        file=SimpleUploadedFile('clip.mp4', b'video data'),
    )
    poster_name = resource.poster.name
    resource.delete()
    assert not resource.poster.storage.exists(poster_name)


EMPTY_META = {
    'title': None,
    'duration': None,
}


@pytest.mark.django_db
def test_upload_audio_files_creates_resources():
    f = SimpleUploadedFile('my-podcast.mp3', b'audio data')
    upload_audio_files([f])
    assert Resource.objects.filter(resource_type=Resource.Type.AUDIO).count() == 1
    resource = Resource.objects.filter(resource_type=Resource.Type.AUDIO).first()
    assert resource.title == 'My Podcast'
    media_file = resource.files.first()
    assert media_file.file_size == len(b'audio data')
    assert media_file.media_type == 'audio/mpeg'


@pytest.mark.django_db
def test_upload_audio_files_stores_duration():
    f = SimpleUploadedFile('episode.mp3', b'audio data')
    meta = {**EMPTY_META, 'duration': timedelta(seconds=90)}
    with patch('curio.resources.use_cases.extract_metadata', return_value=meta):
        upload_audio_files([f])
    resource = Resource.objects.filter(resource_type=Resource.Type.AUDIO).first()
    assert resource.files.first().duration == timedelta(seconds=90)


@pytest.mark.django_db
def test_upload_audio_files_stores_none_duration_when_unreadable():
    f = SimpleUploadedFile('episode.mp3', b'not real audio')
    upload_audio_files([f])
    resource = Resource.objects.filter(resource_type=Resource.Type.AUDIO).first()
    assert resource.files.first().duration is None


@pytest.mark.django_db
def test_upload_audio_files_uses_id3_title_when_available():
    f = SimpleUploadedFile('my-podcast.mp3', b'audio data')
    with patch(
        'curio.resources.use_cases.extract_metadata',
        return_value={**EMPTY_META, 'title': 'Custom Tag Title'},
    ):
        upload_audio_files([f])
    assert (
        Resource.objects.filter(resource_type=Resource.Type.AUDIO).first().title
        == 'Custom Tag Title'
    )


@pytest.mark.django_db
def test_upload_audio_files_derives_title_from_filename():
    cases = [
        ('my-podcast.mp3', 'My Podcast'),
        ('another_episode.mp3', 'Another Episode'),
        ('simple.mp3', 'Simple'),
    ]
    for filename, expected_title in cases:
        upload_audio_files([SimpleUploadedFile(filename, b'data')])
    titles = set(
        Resource.objects.filter(resource_type=Resource.Type.AUDIO).values_list(
            'title', flat=True
        )
    )
    assert titles == {'My Podcast', 'Another Episode', 'Simple'}


EMPTY_IMAGE_META = {
    'width': None,
    'height': None,
    'format': None,
    'color_mode': None,
    'icc_profile': None,
    'taken_at': None,
    'camera_make': None,
    'camera_model': None,
    'lens': None,
    'aperture': None,
    'shutter_speed': None,
    'focal_length': None,
}


@pytest.mark.django_db
def test_upload_image_files_creates_resources():
    f = SimpleUploadedFile('my-photo.jpg', b'image data')
    with patch(
        'curio.resources.use_cases.extract_image_metadata',
        return_value=EMPTY_IMAGE_META,
    ):
        upload_image_files([f])
    assert Resource.objects.filter(resource_type=Resource.Type.IMAGE).count() == 1
    resource = Resource.objects.filter(resource_type=Resource.Type.IMAGE).first()
    assert resource.title == 'My Photo'
    media_file = resource.files.first()
    assert media_file.file_size == len(b'image data')
    assert media_file.media_type == 'image/jpeg'


@pytest.mark.django_db
def test_upload_image_files_stores_dimensions():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'width': 1920, 'height': 1080}
    with patch('curio.resources.use_cases.extract_image_metadata', return_value=meta):
        upload_image_files([f])
    media_file = (
        Resource.objects.filter(resource_type=Resource.Type.IMAGE).first().files.first()
    )
    assert media_file.width == 1920
    assert media_file.height == 1080


@pytest.mark.django_db
def test_upload_image_files_stores_technical_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {
        **EMPTY_IMAGE_META,
        'format': 'JPEG',
        'color_mode': 'RGB',
        'icc_profile': 'sRGB',
    }
    with patch('curio.resources.use_cases.extract_image_metadata', return_value=meta):
        upload_image_files([f])
    resource = Resource.objects.filter(resource_type=Resource.Type.IMAGE).first()
    exif = resource.metadata.get(type=Metadata.Type.EXIF)
    assert exif.data['format'] == 'JPEG'
    assert exif.data['color_mode'] == 'RGB'
    assert exif.data['icc_profile'] == 'sRGB'


@pytest.mark.django_db
def test_upload_image_files_stores_exif_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    taken = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    meta = {
        **EMPTY_IMAGE_META,
        'taken_at': taken,
        'camera_make': 'Canon',
        'camera_model': 'EOS R5',
    }
    with patch('curio.resources.use_cases.extract_image_metadata', return_value=meta):
        upload_image_files([f])
    resource = Resource.objects.filter(resource_type=Resource.Type.IMAGE).first()
    assert resource.produced_at == taken
    exif = resource.metadata.get(type=Metadata.Type.EXIF)
    assert exif.data['camera_make'] == 'Canon'
    assert exif.data['camera_model'] == 'EOS R5'


@pytest.mark.django_db
def test_upload_image_files_stores_lens_and_exposure_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {
        **EMPTY_IMAGE_META,
        'lens': 'EF 50mm f/1.4 USM',
        'aperture': 1.4,
        'shutter_speed': '1/250',
        'focal_length': 50.0,
    }
    with patch('curio.resources.use_cases.extract_image_metadata', return_value=meta):
        upload_image_files([f])
    resource = Resource.objects.filter(resource_type=Resource.Type.IMAGE).first()
    exif = resource.metadata.get(type=Metadata.Type.EXIF)
    assert exif.data['lens'] == 'EF 50mm f/1.4 USM'
    assert exif.data['aperture'] == 1.4
    assert exif.data['shutter_speed'] == '1/250'
    assert exif.data['focal_length'] == 50.0


@pytest.mark.django_db
def test_upload_image_files_stores_none_metadata_when_unreadable():
    f = SimpleUploadedFile('photo.jpg', b'not real image')
    upload_image_files([f])
    resource = Resource.objects.filter(resource_type=Resource.Type.IMAGE).first()
    media_file = resource.files.first()
    assert media_file.width is None
    assert media_file.height is None
    assert resource.produced_at is None
    assert resource.metadata.count() == 0


@pytest.mark.django_db
def test_upload_image_files_derives_title_from_filename():
    cases = [
        ('my-photo.jpg', 'My Photo'),
        ('beach_sunset.png', 'Beach Sunset'),
        ('portrait.jpg', 'Portrait'),
    ]
    for filename, _ in cases:
        with patch(
            'curio.resources.use_cases.extract_image_metadata',
            return_value=EMPTY_IMAGE_META,
        ):
            upload_image_files([SimpleUploadedFile(filename, b'data')])
    titles = set(
        Resource.objects.filter(resource_type=Resource.Type.IMAGE).values_list(
            'title', flat=True
        )
    )
    assert titles == {'My Photo', 'Beach Sunset', 'Portrait'}


EMPTY_VIDEO_META = {
    'duration': None,
    'width': None,
    'height': None,
}


@pytest.mark.django_db
def test_upload_video_files_creates_resources():
    f = SimpleUploadedFile('my-video.mp4', b'video data')
    with patch(
        'curio.resources.use_cases.extract_video_metadata',
        return_value=EMPTY_VIDEO_META,
    ):
        upload_video_files([f])
    assert Resource.objects.filter(resource_type=Resource.Type.VIDEO).count() == 1
    resource = Resource.objects.filter(resource_type=Resource.Type.VIDEO).first()
    assert resource.title == 'My Video'
    media_file = resource.files.first()
    assert media_file.file_size == len(b'video data')
    assert media_file.media_type == 'video/mp4'


@pytest.mark.django_db
def test_upload_video_files_stores_duration_and_dimensions():
    f = SimpleUploadedFile('video.mp4', b'video data')
    meta = {
        **EMPTY_VIDEO_META,
        'duration': timedelta(seconds=120),
        'width': 1920,
        'height': 1080,
    }
    with patch('curio.resources.use_cases.extract_video_metadata', return_value=meta):
        upload_video_files([f])
    media_file = (
        Resource.objects.filter(resource_type=Resource.Type.VIDEO).first().files.first()
    )
    assert media_file.duration == timedelta(seconds=120)
    assert media_file.width == 1920
    assert media_file.height == 1080


@pytest.mark.django_db
def test_upload_video_files_stores_none_metadata_when_unreadable():
    f = SimpleUploadedFile('video.mp4', b'not real video')
    upload_video_files([f])
    media_file = (
        Resource.objects.filter(resource_type=Resource.Type.VIDEO).first().files.first()
    )
    assert media_file.duration is None
    assert media_file.width is None


@pytest.mark.django_db
def test_upload_video_files_derives_title_from_filename():
    cases = [
        ('my-video.mp4', 'My Video'),
        ('beach_holiday.mov', 'Beach Holiday'),
        ('intro.mp4', 'Intro'),
    ]
    for filename, _ in cases:
        with patch(
            'curio.resources.use_cases.extract_video_metadata',
            return_value=EMPTY_VIDEO_META,
        ):
            upload_video_files([SimpleUploadedFile(filename, b'data')])
    titles = set(
        Resource.objects.filter(resource_type=Resource.Type.VIDEO).values_list(
            'title', flat=True
        )
    )
    assert titles == {'My Video', 'Beach Holiday', 'Intro'}


# --- resource_detail view ---


@pytest.mark.django_db
@pytest.mark.parametrize(
    'resource_type',
    [
        Resource.Type.IMAGE,
        Resource.Type.AUDIO,
        Resource.Type.VIDEO,
        Resource.Type.DOCUMENT,
    ],
)
def test_resource_detail_returns_200(client, resource_type):
    resource = Resource.objects.create(resource_type=resource_type, title='Test')
    response = client.get(reverse('resource_detail', args=[resource.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_resource_detail_returns_404_for_unknown_pk(client):
    response = client.get(reverse('resource_detail', args=[99999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_resource_detail_shows_title(client):
    resource = Resource.objects.create(
        resource_type=Resource.Type.AUDIO, title='My Podcast'
    )
    response = client.get(reverse('resource_detail', args=[resource.pk]))
    assert b'My Podcast' in response.content


@pytest.mark.django_db
def test_resource_detail_context_contains_resource(client):
    resource = Resource.objects.create(resource_type=Resource.Type.IMAGE, title='Photo')
    response = client.get(reverse('resource_detail', args=[resource.pk]))
    assert response.context['resource'] == resource
