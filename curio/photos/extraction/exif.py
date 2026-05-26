from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from pathlib import Path

from django.utils import timezone
from PIL import Image

_TAG_MAKE = 271
_TAG_MODEL = 272
_TAG_DATETIME_ORIGINAL = 36867
_TAG_FNUMBER = 33437
_TAG_EXPOSURE_TIME = 33434
_TAG_FOCAL_LENGTH = 37386
_TAG_LENS_MODEL = 42036
_EXIF_IFD = 0x8769


@dataclass
class ExifData:
    taken_at: datetime | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens: str | None = None
    aperture: float | None = None
    exposure_time: float | None = None
    focal_length: float | None = None

    @property
    def shutter_speed(self) -> str | None:
        if self.exposure_time is None:
            return None
        frac = Fraction(self.exposure_time).limit_denominator(100000)
        if frac.denominator == 1:
            return str(frac.numerator)
        return f'{frac.numerator}/{frac.denominator}'


def extract_exif(img: Image.Image | Path) -> ExifData:
    if isinstance(img, Path):
        img = Image.open(img)
        img.load()
    try:
        exif = img.getexif()
    except Exception:
        return ExifData()

    result = ExifData()
    try:
        taken_str = exif.get(_TAG_DATETIME_ORIGINAL)
        if taken_str:
            naive = datetime.strptime(taken_str, '%Y:%m:%d %H:%M:%S')
            result.taken_at = timezone.make_aware(naive)
        result.camera_make = exif.get(_TAG_MAKE) or None
        result.camera_model = exif.get(_TAG_MODEL) or None
        ifd = exif.get_ifd(_EXIF_IFD)
        result.lens = ifd.get(_TAG_LENS_MODEL) or None
        raw_aperture = ifd.get(_TAG_FNUMBER)
        if raw_aperture is not None:
            result.aperture = float(raw_aperture)
        raw_exposure_time = ifd.get(_TAG_EXPOSURE_TIME)
        if raw_exposure_time is not None:
            result.exposure_time = float(raw_exposure_time)
        raw_focal = ifd.get(_TAG_FOCAL_LENGTH)
        if raw_focal is not None:
            result.focal_length = float(raw_focal)
    except Exception:
        pass
    return result
