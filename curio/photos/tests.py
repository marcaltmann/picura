from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Metadata, Photo
from .use_cases import upload_photos


@pytest.mark.django_db
def test_metadata_can_be_attached_to_photo():
    photo = Photo.objects.create(title='Photo', file_size=0)
    meta = Metadata.objects.create(
        photo=photo,
        type=Metadata.Type.EXIF,
        data={'Make': 'Canon', 'Model': 'EOS R5'},
    )
    assert photo.metadata.count() == 1
    assert photo.metadata.first() == meta


@pytest.mark.django_db
def test_metadata_deleted_with_photo():
    photo = Photo.objects.create(title='Photo', file_size=0)
    Metadata.objects.create(photo=photo, type=Metadata.Type.CUSTOM, data={'foo': 'bar'})
    photo.delete()
    assert Metadata.objects.count() == 0


@pytest.mark.django_db
def test_multiple_metadata_types_per_photo():
    photo = Photo.objects.create(title='Photo', file_size=0)
    Metadata.objects.create(photo=photo, type=Metadata.Type.EXIF, data={'ISO': 400})
    Metadata.objects.create(
        photo=photo, type=Metadata.Type.DUBLIN_CORE, data={'creator': 'Bob'}
    )
    assert photo.metadata.count() == 2
    types = set(photo.metadata.values_list('type', flat=True))
    assert types == {Metadata.Type.EXIF, Metadata.Type.DUBLIN_CORE}


@pytest.mark.django_db
def test_deleting_photo_deletes_file():
    photo = Photo.objects.create(
        title='Photo',
        file=SimpleUploadedFile('photo.jpg', b'image data'),
    )
    name = photo.file.name
    photo.delete()
    assert not photo.file.storage.exists(name)


EMPTY_IMAGE_META = {
    'title': None,
    'description': None,
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
    'latitude': None,
    'longitude': None,
}


@pytest.mark.django_db
def test_upload_photos_creates_photo():
    f = SimpleUploadedFile('my-photo.jpg', b'image data')
    with patch(
        'curio.photos.use_cases.extract_image_metadata',
        return_value=EMPTY_IMAGE_META,
    ):
        upload_photos([f])
    assert Photo.objects.count() == 1
    photo = Photo.objects.first()
    assert photo.title == 'My Photo'
    assert photo.file_size == len(b'image data')
    assert photo.media_type == 'image/jpeg'


@pytest.mark.django_db
def test_upload_photos_stores_dimensions():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'width': 1920, 'height': 1080}
    with patch('curio.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    photo = Photo.objects.first()
    assert photo.width == 1920
    assert photo.height == 1080


@pytest.mark.django_db
def test_upload_photos_stores_technical_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {
        **EMPTY_IMAGE_META,
        'format': 'JPEG',
        'color_mode': 'RGB',
        'icc_profile': 'sRGB',
    }
    with patch('curio.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    photo = Photo.objects.first()
    exif = photo.metadata.get(type=Metadata.Type.EXIF)
    assert exif.data['format'] == 'JPEG'
    assert exif.data['color_mode'] == 'RGB'
    assert exif.data['icc_profile'] == 'sRGB'


@pytest.mark.django_db
def test_upload_photos_stores_exif_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    taken = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    meta = {
        **EMPTY_IMAGE_META,
        'taken_at': taken,
        'camera_make': 'Canon',
        'camera_model': 'EOS R5',
    }
    with patch('curio.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    photo = Photo.objects.first()
    assert photo.produced_at == taken
    exif = photo.metadata.get(type=Metadata.Type.EXIF)
    assert exif.data['camera_make'] == 'Canon'
    assert exif.data['camera_model'] == 'EOS R5'


@pytest.mark.django_db
def test_upload_photos_stores_lens_and_exposure_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {
        **EMPTY_IMAGE_META,
        'lens': 'EF 50mm f/1.4 USM',
        'aperture': 1.4,
        'shutter_speed': '1/250',
        'focal_length': 50.0,
    }
    with patch('curio.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    photo = Photo.objects.first()
    exif = photo.metadata.get(type=Metadata.Type.EXIF)
    assert exif.data['lens'] == 'EF 50mm f/1.4 USM'
    assert exif.data['aperture'] == 1.4
    assert exif.data['shutter_speed'] == '1/250'
    assert exif.data['focal_length'] == 50.0


@pytest.mark.django_db
def test_upload_photos_stores_none_metadata_when_unreadable():
    f = SimpleUploadedFile('photo.jpg', b'not real image')
    upload_photos([f])
    photo = Photo.objects.first()
    assert photo.width is None
    assert photo.height is None
    assert photo.produced_at is None
    assert photo.metadata.count() == 0


@pytest.mark.django_db
def test_upload_photos_derives_title_from_filename():
    cases = [
        ('my-photo.jpg', 'My Photo'),
        ('beach_sunset.png', 'Beach Sunset'),
        ('portrait.jpg', 'Portrait'),
    ]
    for filename, _ in cases:
        with patch(
            'curio.photos.use_cases.extract_image_metadata',
            return_value=EMPTY_IMAGE_META,
        ):
            upload_photos([SimpleUploadedFile(filename, b'data')])
    titles = set(Photo.objects.values_list('title', flat=True))
    assert titles == {'My Photo', 'Beach Sunset', 'Portrait'}


@pytest.mark.django_db
def test_upload_photos_uses_metadata_title_when_available():
    f = SimpleUploadedFile('my-photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'title': 'Sunset Over the Lake'}
    with patch('curio.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    assert Photo.objects.first().title == 'Sunset Over the Lake'


@pytest.mark.django_db
def test_upload_photos_stores_description_from_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'description': 'A beautiful landscape at dusk.'}
    with patch('curio.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    assert Photo.objects.first().description == 'A beautiful landscape at dusk.'


@pytest.mark.django_db
def test_upload_photos_leaves_description_blank_when_absent():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    with patch(
        'curio.photos.use_cases.extract_image_metadata',
        return_value=EMPTY_IMAGE_META,
    ):
        upload_photos([f])
    assert Photo.objects.first().description == ''
