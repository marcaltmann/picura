from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from .exif import ExifData, extract_exif

_TAG_MAKE = 271
_TAG_MODEL = 272
_TAG_DATETIME_ORIGINAL = 36867
_TAG_FNUMBER = 33437
_TAG_EXPOSURE_TIME = 33434
_TAG_FOCAL_LENGTH = 37386
_TAG_LENS_MODEL = 42036
_EXIF_IFD_TAG = 0x8769
_GPS_IFD_TAG = 0x8825


class FakeExif:
    def __init__(self, data=None, ifd=None, gps_ifd=None):
        self._data = data or {}
        self._ifds = {
            _EXIF_IFD_TAG: ifd or {},
            _GPS_IFD_TAG: gps_ifd or {},
        }

    def get(self, tag, default=None):
        return self._data.get(tag, default)

    def get_ifd(self, tag):
        return self._ifds.get(tag, {})


def make_img(exif=None):
    img = MagicMock()
    img.getexif.return_value = exif or FakeExif()
    return img


def test_accepts_path_object(tmp_path):
    from PIL import Image as PilImage

    img = PilImage.new('RGB', (1, 1))
    path = tmp_path / 'test.jpg'
    img.save(path)
    result = extract_exif(path)
    assert result == ExifData()


def test_raises_when_path_does_not_exist():
    with pytest.raises(FileNotFoundError):
        extract_exif(Path('/nonexistent/image.jpg'))


def test_returns_empty_dataclass_on_getexif_exception():
    img = MagicMock()
    img.getexif.side_effect = Exception('no exif')
    assert extract_exif(img) == ExifData()


def test_returns_empty_dataclass_when_no_data():
    assert extract_exif(make_img()) == ExifData()


def test_extracts_camera_make():
    exif = FakeExif(data={_TAG_MAKE: 'Canon'})
    result = extract_exif(make_img(exif))
    assert result.camera_make == 'Canon'


def test_extracts_camera_model():
    exif = FakeExif(data={_TAG_MODEL: 'EOS R5'})
    result = extract_exif(make_img(exif))
    assert result.camera_model == 'EOS R5'


def test_extracts_lens():
    exif = FakeExif(ifd={_TAG_LENS_MODEL: 'EF 50mm f/1.4 USM'})
    result = extract_exif(make_img(exif))
    assert result.lens == 'EF 50mm f/1.4 USM'


def test_extracts_aperture_as_float():
    exif = FakeExif(ifd={_TAG_FNUMBER: Fraction(14, 10)})
    result = extract_exif(make_img(exif))
    assert result.aperture == pytest.approx(1.4)


def test_extracts_shutter_speed_as_fraction_string():
    exif = FakeExif(ifd={_TAG_EXPOSURE_TIME: Fraction(1, 250)})
    result = extract_exif(make_img(exif))
    assert result.shutter_speed == '1/250'


def test_extracts_shutter_speed_as_whole_number():
    exif = FakeExif(ifd={_TAG_EXPOSURE_TIME: Fraction(30, 1)})
    result = extract_exif(make_img(exif))
    assert result.shutter_speed == '30'


def test_extracts_focal_length_as_float():
    exif = FakeExif(ifd={_TAG_FOCAL_LENGTH: Fraction(50, 1)})
    result = extract_exif(make_img(exif))
    assert result.focal_length == pytest.approx(50.0)


def test_extracts_taken_at_as_aware_datetime():
    exif = FakeExif(data={_TAG_DATETIME_ORIGINAL: '2024:06:15 10:30:00'})
    result = extract_exif(make_img(exif))
    assert result.taken_at is not None
    assert result.taken_at.tzinfo is not None
    assert result.taken_at.replace(tzinfo=None) == datetime(2024, 6, 15, 10, 30, 0)


def test_missing_fields_are_none():
    result = extract_exif(make_img())
    assert result.camera_make is None
    assert result.camera_model is None
    assert result.lens is None
    assert result.aperture is None
    assert result.shutter_speed is None
    assert result.focal_length is None
    assert result.taken_at is None
    assert result.latitude is None
    assert result.longitude is None


def test_empty_string_camera_make_becomes_none():
    exif = FakeExif(data={_TAG_MAKE: ''})
    result = extract_exif(make_img(exif))
    assert result.camera_make is None


def test_extracts_gps_coordinates():
    exif = FakeExif(
        gps_ifd={
            1: 'N',
            2: (Fraction(52), Fraction(31), Fraction(0)),
            3: 'E',
            4: (Fraction(13), Fraction(24), Fraction(0)),
        }
    )
    result = extract_exif(make_img(exif))
    assert result.latitude == pytest.approx(52.0 + 31 / 60)
    assert result.longitude == pytest.approx(13.0 + 24 / 60)


def test_gps_south_west_becomes_negative():
    exif = FakeExif(
        gps_ifd={
            1: 'S',
            2: (Fraction(33), Fraction(52), Fraction(0)),
            3: 'W',
            4: (Fraction(70), Fraction(40), Fraction(12)),
        }
    )
    result = extract_exif(make_img(exif))
    assert result.latitude == pytest.approx(-(33.0 + 52 / 60))
    assert result.longitude == pytest.approx(-(70.0 + 40 / 60 + 12 / 3600))


def test_gps_missing_ref_yields_none():
    exif = FakeExif(
        gps_ifd={
            2: (Fraction(52), Fraction(31), Fraction(0)),
            4: (Fraction(13), Fraction(24), Fraction(0)),
        }
    )
    result = extract_exif(make_img(exif))
    assert result.latitude is None
    assert result.longitude is None


def test_extracts_all_fields_together():
    exif = FakeExif(
        data={
            _TAG_MAKE: 'Nikon',
            _TAG_MODEL: 'Z9',
            _TAG_DATETIME_ORIGINAL: '2024:01:20 08:15:30',
        },
        ifd={
            _TAG_LENS_MODEL: 'NIKKOR Z 24-70mm f/2.8 S',
            _TAG_FNUMBER: Fraction(28, 10),
            _TAG_EXPOSURE_TIME: Fraction(1, 125),
            _TAG_FOCAL_LENGTH: Fraction(35, 1),
        },
    )
    result = extract_exif(make_img(exif))
    assert result.camera_make == 'Nikon'
    assert result.camera_model == 'Z9'
    assert result.lens == 'NIKKOR Z 24-70mm f/2.8 S'
    assert result.aperture == pytest.approx(2.8)
    assert result.shutter_speed == '1/125'
    assert result.focal_length == pytest.approx(35.0)
    assert result.taken_at is not None
    assert result.taken_at.replace(tzinfo=None) == datetime(2024, 1, 20, 8, 15, 30)
