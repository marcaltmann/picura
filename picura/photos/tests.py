import io
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from .models import Metadata, Photo, PhotoExif, Batch
from .use_cases import upload_photos


def _make_batch():
    return Batch.objects.create()


def _make_photo(**kwargs):
    img = Image.new('RGB', (1, 1), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    f = SimpleUploadedFile('photo.jpg', buf.read(), content_type='image/jpeg')
    batch = kwargs.pop('batch', None) or _make_batch()
    return Photo.objects.create(file=f, **{'title': 'Photo', 'batch': batch, **kwargs})


@pytest.mark.django_db
def test_metadata_can_be_attached_to_photo():
    photo = Photo.objects.create(title='Photo', file_size=0, batch=_make_batch())
    meta = Metadata.objects.create(
        photo=photo,
        type=Metadata.Type.EXIF,
        data={'Make': 'Canon', 'Model': 'EOS R5'},
    )
    assert photo.metadata.count() == 1
    assert photo.metadata.first() == meta


@pytest.mark.django_db
def test_metadata_deleted_with_photo():
    photo = Photo.objects.create(title='Photo', file_size=0, batch=_make_batch())
    Metadata.objects.create(photo=photo, type=Metadata.Type.CUSTOM, data={'foo': 'bar'})
    photo.delete()
    assert Metadata.objects.count() == 0


@pytest.mark.django_db
def test_multiple_metadata_types_per_photo():
    photo = Photo.objects.create(title='Photo', file_size=0, batch=_make_batch())
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
        batch=_make_batch(),
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
    'exposure_time': None,
    'shutter_speed': None,
    'focal_length': None,
    'iso': None,
    'latitude': None,
    'longitude': None,
    'keywords': [],
    'copyright': None,
    'creator': None,
    'raw': {},
}


@pytest.mark.django_db
def test_upload_photos_creates_batch_and_links_photos():
    files = [
        SimpleUploadedFile('a.jpg', b'image data'),
        SimpleUploadedFile('b.jpg', b'image data'),
    ]
    with patch(
        'picura.photos.use_cases.extract_image_metadata',
        return_value=EMPTY_IMAGE_META,
    ):
        upload_photos(files)
    assert Batch.objects.count() == 1
    batch = Batch.objects.first()
    assert batch.photos.count() == 2


@pytest.mark.django_db
def test_upload_photos_creates_photo():
    f = SimpleUploadedFile('my-photo.jpg', b'image data')
    with patch(
        'picura.photos.use_cases.extract_image_metadata',
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
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    photo = Photo.objects.first()
    assert photo.width == 1920
    assert photo.height == 1080


@pytest.mark.django_db
def test_upload_photos_stores_produced_at_from_taken_at():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    taken = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    meta = {**EMPTY_IMAGE_META, 'taken_at': taken, 'raw': {'Make': 'Canon'}}
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    assert Photo.objects.first().produced_at == taken


@pytest.mark.django_db
def test_upload_photos_creates_photo_exif():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {
        **EMPTY_IMAGE_META,
        'camera_make': 'Canon',
        'camera_model': 'EOS R5',
        'lens': 'EF 50mm f/1.4 USM',
        'aperture': 1.4,
        'exposure_time': 0.004,
        'focal_length': 50.0,
        'iso': 400,
        'raw': {'Make': 'Canon', 'Model': 'EOS R5'},
    }
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    exif = Photo.objects.first().exif
    assert exif.camera_make == 'Canon'
    assert exif.camera_model == 'EOS R5'
    assert exif.lens == 'EF 50mm f/1.4 USM'
    assert exif.aperture == 1.4
    assert exif.exposure_time == 0.004
    assert exif.shutter_speed == '1/250'
    assert exif.focal_length == 50.0
    assert exif.iso == 400
    assert exif.raw == {'Make': 'Canon', 'Model': 'EOS R5'}


@pytest.mark.django_db
def test_upload_photos_stores_geo_coordinates():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {
        **EMPTY_IMAGE_META,
        'latitude': -33.85,
        'longitude': -70.66,
        'raw': {'GPSLatitude': -33.85},
    }
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    exif = Photo.objects.first().exif
    assert exif.latitude == -33.85
    assert exif.longitude == -70.66


@pytest.mark.django_db
def test_upload_photos_skips_photo_exif_when_no_raw():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    with patch(
        'picura.photos.use_cases.extract_image_metadata',
        return_value=EMPTY_IMAGE_META,
    ):
        upload_photos([f])
    assert not PhotoExif.objects.exists()


@pytest.mark.django_db
def test_upload_photos_stores_dublin_core_from_iptc():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {
        **EMPTY_IMAGE_META,
        'creator': 'Marc Altmann',
        'copyright': '© Marc',
        'keywords': ['lake', 'dusk'],
    }
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    dc = Photo.objects.first().metadata.get(type=Metadata.Type.DUBLIN_CORE)
    assert dc.data['creator'] == 'Marc Altmann'
    assert dc.data['copyright'] == '© Marc'
    assert dc.data['keywords'] == ['lake', 'dusk']


@pytest.mark.django_db
def test_upload_photos_skips_dublin_core_when_absent():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'raw': {'Make': 'Canon'}}
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    assert not Metadata.objects.filter(type=Metadata.Type.DUBLIN_CORE).exists()


@pytest.mark.django_db
def test_upload_photos_stores_none_metadata_when_unreadable():
    f = SimpleUploadedFile('photo.jpg', b'not real image')
    upload_photos([f])
    photo = Photo.objects.first()
    assert photo.width is None
    assert photo.height is None
    assert photo.produced_at is None
    assert photo.metadata.count() == 0
    assert not PhotoExif.objects.exists()


@pytest.mark.django_db
def test_upload_photos_derives_title_from_filename():
    cases = [
        ('my-photo.jpg', 'My Photo'),
        ('beach_sunset.png', 'Beach Sunset'),
        ('portrait.jpg', 'Portrait'),
    ]
    for filename, _ in cases:
        with patch(
            'picura.photos.use_cases.extract_image_metadata',
            return_value=EMPTY_IMAGE_META,
        ):
            upload_photos([SimpleUploadedFile(filename, b'data')])
    titles = set(Photo.objects.values_list('title', flat=True))
    assert titles == {'My Photo', 'Beach Sunset', 'Portrait'}


@pytest.mark.django_db
def test_upload_photos_uses_metadata_title_when_available():
    f = SimpleUploadedFile('my-photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'title': 'Sunset Over the Lake'}
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    assert Photo.objects.first().title == 'Sunset Over the Lake'


@pytest.mark.django_db
def test_upload_photos_stores_description_from_metadata():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    meta = {**EMPTY_IMAGE_META, 'description': 'A beautiful landscape at dusk.'}
    with patch('picura.photos.use_cases.extract_image_metadata', return_value=meta):
        upload_photos([f])
    assert Photo.objects.first().description == 'A beautiful landscape at dusk.'


@pytest.mark.django_db
def test_upload_photos_leaves_description_blank_when_absent():
    f = SimpleUploadedFile('photo.jpg', b'image data')
    with patch(
        'picura.photos.use_cases.extract_image_metadata',
        return_value=EMPTY_IMAGE_META,
    ):
        upload_photos([f])
    assert Photo.objects.first().description == ''


# --- PhotoExif model ---


@pytest.mark.django_db
def test_photo_exif_round_trips_typed_fields():
    photo = Photo.objects.create(title='Photo', file_size=0, batch=_make_batch())
    exif = PhotoExif.objects.create(
        photo=photo,
        camera_make='Canon',
        camera_model='EOS R5',
        lens='EF 50mm f/1.4 USM',
        aperture=1.4,
        exposure_time=0.004,
        focal_length=50.0,
        iso=400,
        latitude=52.52,
        longitude=13.405,
        raw={'foo': 'bar'},
    )
    exif.refresh_from_db()
    assert photo.exif == exif
    assert exif.camera_make == 'Canon'
    assert exif.aperture == 1.4
    assert exif.iso == 400
    assert exif.latitude == 52.52
    assert exif.longitude == 13.405
    assert exif.raw == {'foo': 'bar'}


@pytest.mark.django_db
def test_photo_exif_deleted_with_photo():
    photo = Photo.objects.create(title='Photo', file_size=0, batch=_make_batch())
    PhotoExif.objects.create(photo=photo)
    photo.delete()
    assert PhotoExif.objects.count() == 0


def test_photo_exif_shutter_speed_formats_fraction():
    assert PhotoExif(exposure_time=0.004).shutter_speed == '1/250'


def test_photo_exif_shutter_speed_whole_seconds():
    assert PhotoExif(exposure_time=2.0).shutter_speed == '2'


def test_photo_exif_shutter_speed_none_when_no_exposure():
    assert PhotoExif().shutter_speed is None


# --- aspect_ratio property ---


def test_aspect_ratio_landscape():
    photo = Photo(title='Test', width=1920, height=1080)
    assert photo.aspect_ratio == pytest.approx(1920 / 1080)


def test_aspect_ratio_portrait():
    photo = Photo(title='Test', width=1080, height=1920)
    assert photo.aspect_ratio == pytest.approx(1080 / 1920)


def test_aspect_ratio_square():
    photo = Photo(title='Test', width=100, height=100)
    assert photo.aspect_ratio == pytest.approx(1.0)


def test_aspect_ratio_none_when_width_missing():
    photo = Photo(title='Test', width=None, height=1080)
    assert photo.aspect_ratio is None


def test_aspect_ratio_none_when_height_missing():
    photo = Photo(title='Test', width=1920, height=None)
    assert photo.aspect_ratio is None


def test_aspect_ratio_none_when_both_missing():
    photo = Photo(title='Test', width=None, height=None)
    assert photo.aspect_ratio is None


# --- display_width property ---


def test_display_width_landscape():
    # 1920x1080 → aspect 16/9 → sqrt(345600 * 16/9) ≈ 784
    photo = Photo(title='Test', width=1920, height=1080)
    import math

    expected = round(math.sqrt(345600 * (1920 / 1080)))
    assert photo.display_width == expected


def test_display_width_portrait():
    # 1080x1920 → aspect 9/16 → sqrt(345600 * 9/16) ≈ 441
    photo = Photo(title='Test', width=1080, height=1920)
    import math

    expected = round(math.sqrt(345600 * (1080 / 1920)))
    assert photo.display_width == expected


def test_display_width_square():
    # 100x100 → aspect 1.0 → sqrt(345600) ≈ 588
    photo = Photo(title='Test', width=100, height=100)
    import math

    expected = round(math.sqrt(345600))
    assert photo.display_width == expected


def test_display_width_none_when_dimensions_missing():
    photo = Photo(title='Test', width=None, height=None)
    assert photo.display_width is None
