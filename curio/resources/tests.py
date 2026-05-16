from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import AudioResource, ImageResource, Metadata, VideoResource
from .use_cases import upload_audio_files, upload_image_files, upload_video_files


@pytest.mark.django_db
def test_metadata_can_be_attached_to_image_resource():
    resource = ImageResource.objects.create(title='Photo', file_size=0)
    meta = Metadata.objects.create(
        resource=resource,
        type=Metadata.Type.EXIF,
        data={'Make': 'Canon', 'Model': 'EOS R5'},
    )
    assert resource.metadata.count() == 1
    assert resource.metadata.first() == meta


@pytest.mark.django_db
def test_metadata_accessible_via_base_resource():
    resource = AudioResource.objects.create(title='Podcast', file_size=0)
    Metadata.objects.create(
        resource=resource,
        type=Metadata.Type.DUBLIN_CORE,
        data={'creator': 'Alice', 'rights': 'CC BY 4.0'},
    )
    assert resource.resource_ptr.metadata.count() == 1


@pytest.mark.django_db
def test_metadata_deleted_with_resource():
    resource = VideoResource.objects.create(title='Clip', file_size=0)
    Metadata.objects.create(
        resource=resource, type=Metadata.Type.CUSTOM, data={'foo': 'bar'}
    )
    resource.delete()
    assert Metadata.objects.count() == 0


@pytest.mark.django_db
def test_multiple_metadata_types_per_resource():
    resource = ImageResource.objects.create(title='Photo', file_size=0)
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
def test_deleting_audio_resource_deletes_file():
    audio = AudioResource.objects.create(
        title='Podcast',
        file=SimpleUploadedFile('ep.mp3', b'audio data'),
    )
    name = audio.file.name
    audio.delete()
    assert not audio.file.storage.exists(name)


@pytest.mark.django_db
def test_deleting_image_resource_deletes_file():
    image = ImageResource.objects.create(
        title='Photo',
        file=SimpleUploadedFile('photo.jpg', b'image data'),
    )
    name = image.file.name
    image.delete()
    assert not image.file.storage.exists(name)


@pytest.mark.django_db
def test_deleting_video_resource_deletes_file_and_poster():
    video = VideoResource.objects.create(
        title='Clip',
        file=SimpleUploadedFile('clip.mp4', b'video data'),
        poster=SimpleUploadedFile('poster.jpg', b'image data'),
    )
    file_name = video.file.name
    poster_name = video.poster.name
    video.delete()
    assert not video.file.storage.exists(file_name)
    assert not video.file.storage.exists(poster_name)


EMPTY_META = {
    'title': None,
    'duration': None,
    'bitrate': None,
    'sample_rate': None,
    'channels': None,
}


@pytest.mark.django_db
def test_upload_audio_files_creates_resources():
    f = SimpleUploadedFile('my-podcast.mp3', b'audio data')
    upload_audio_files([f])
    assert AudioResource.objects.count() == 1
    resource = AudioResource.objects.first()
    assert resource.title == 'My Podcast'
    assert resource.file_size == len(b'audio data')


@pytest.mark.django_db
def test_upload_audio_files_stores_duration():
    f = SimpleUploadedFile('episode.mp3', b'audio data')
    meta = {**EMPTY_META, 'duration': timedelta(seconds=90)}
    with patch('curio.resources.use_cases.extract_metadata', return_value=meta):
        upload_audio_files([f])
    assert AudioResource.objects.first().duration == timedelta(seconds=90)


@pytest.mark.django_db
def test_upload_audio_files_stores_technical_metadata():
    f = SimpleUploadedFile('episode.mp3', b'audio data')
    meta = {**EMPTY_META, 'bitrate': 128000, 'sample_rate': 44100, 'channels': 2}
    with patch('curio.resources.use_cases.extract_metadata', return_value=meta):
        upload_audio_files([f])
    resource = AudioResource.objects.first()
    assert resource.bitrate == 128000
    assert resource.sample_rate == 44100
    assert resource.channels == 2


@pytest.mark.django_db
def test_upload_audio_files_stores_none_metadata_when_unreadable():
    f = SimpleUploadedFile('episode.mp3', b'not real audio')
    upload_audio_files([f])
    resource = AudioResource.objects.first()
    assert resource.duration is None
    assert resource.bitrate is None
    assert resource.sample_rate is None
    assert resource.channels is None


@pytest.mark.django_db
def test_upload_audio_files_uses_id3_title_when_available():
    f = SimpleUploadedFile('my-podcast.mp3', b'audio data')
    with patch(
        'curio.resources.use_cases.extract_metadata',
        return_value={**EMPTY_META, 'title': 'Custom Tag Title'},
    ):
        upload_audio_files([f])
    assert AudioResource.objects.first().title == 'Custom Tag Title'


@pytest.mark.django_db
def test_upload_audio_files_derives_title_from_filename():
    cases = [
        ('my-podcast.mp3', 'My Podcast'),
        ('another_episode.mp3', 'Another Episode'),
        ('simple.mp3', 'Simple'),
    ]
    for filename, expected_title in cases:
        upload_audio_files([SimpleUploadedFile(filename, b'data')])
    titles = set(AudioResource.objects.values_list('title', flat=True))
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
    assert ImageResource.objects.count() == 1
    resource = ImageResource.objects.first()
    assert resource.title == 'My Photo'
    assert resource.file_size == len(b'image data')


@pytest.mark.django_db
def test_upload_image_files_stores_dimensions():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'width': 1920, 'height': 1080}
    with patch('curio.resources.use_cases.extract_image_metadata', return_value=meta):
        upload_image_files([f])
    resource = ImageResource.objects.first()
    assert resource.width == 1920
    assert resource.height == 1080


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
    resource = ImageResource.objects.first()
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
    resource = ImageResource.objects.first()
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
    exif = ImageResource.objects.first().metadata.get(type=Metadata.Type.EXIF)
    assert exif.data['lens'] == 'EF 50mm f/1.4 USM'
    assert exif.data['aperture'] == 1.4
    assert exif.data['shutter_speed'] == '1/250'
    assert exif.data['focal_length'] == 50.0


@pytest.mark.django_db
def test_upload_image_files_stores_none_metadata_when_unreadable():
    f = SimpleUploadedFile('photo.jpg', b'not real image')
    upload_image_files([f])
    resource = ImageResource.objects.first()
    assert resource.width is None
    assert resource.height is None
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
    titles = set(ImageResource.objects.values_list('title', flat=True))
    assert titles == {'My Photo', 'Beach Sunset', 'Portrait'}


EMPTY_VIDEO_META = {
    'duration': None,
    'width': None,
    'height': None,
    'bitrate': None,
    'video_codec': None,
    'frame_rate_num': None,
    'frame_rate_den': None,
    'audio_codec': None,
}


@pytest.mark.django_db
def test_upload_video_files_creates_resources():
    f = SimpleUploadedFile('my-video.mp4', b'video data')
    with patch(
        'curio.resources.use_cases.extract_video_metadata',
        return_value=EMPTY_VIDEO_META,
    ):
        upload_video_files([f])
    assert VideoResource.objects.count() == 1
    resource = VideoResource.objects.first()
    assert resource.title == 'My Video'
    assert resource.file_size == len(b'video data')


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
    resource = VideoResource.objects.first()
    assert resource.duration == timedelta(seconds=120)
    assert resource.width == 1920
    assert resource.height == 1080


@pytest.mark.django_db
def test_upload_video_files_stores_codec_metadata():
    f = SimpleUploadedFile('video.mp4', b'video data')
    meta = {
        **EMPTY_VIDEO_META,
        'video_codec': 'h264',
        'audio_codec': 'aac',
        'bitrate': 5000000,
    }
    with patch('curio.resources.use_cases.extract_video_metadata', return_value=meta):
        upload_video_files([f])
    resource = VideoResource.objects.first()
    assert resource.video_codec == 'h264'
    assert resource.audio_codec == 'aac'
    assert resource.bitrate == 5000000


@pytest.mark.django_db
def test_upload_video_files_stores_frame_rate():
    f = SimpleUploadedFile('video.mp4', b'video data')
    meta = {**EMPTY_VIDEO_META, 'frame_rate_num': 30000, 'frame_rate_den': 1001}
    with patch('curio.resources.use_cases.extract_video_metadata', return_value=meta):
        upload_video_files([f])
    resource = VideoResource.objects.first()
    assert resource.frame_rate_num == 30000
    assert resource.frame_rate_den == 1001


@pytest.mark.django_db
def test_upload_video_files_stores_none_metadata_when_unreadable():
    f = SimpleUploadedFile('video.mp4', b'not real video')
    upload_video_files([f])
    resource = VideoResource.objects.first()
    assert resource.duration is None
    assert resource.width is None
    assert resource.video_codec is None
    assert resource.frame_rate_num is None


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
    titles = set(VideoResource.objects.values_list('title', flat=True))
    assert titles == {'My Video', 'Beach Holiday', 'Intro'}
