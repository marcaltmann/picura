import io
import json
import mimetypes
import subprocess
import tempfile
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

import mutagen
from PIL import Image, ImageCms

from .models import MediaFile, Metadata, Resource


def extract_metadata(file):
    result = {
        'title': None,
        'duration': None,
    }
    try:
        audio = mutagen.File(file, easy=True)
    except mutagen.MutagenError:
        return result
    if audio is None:
        return result
    if audio.tags:
        titles = audio.tags.get('title')
        if titles:
            result['title'] = titles[0]
    if audio.info:
        result['duration'] = timedelta(seconds=audio.info.length)
    return result


_EXIF_TAG_MAKE = 271
_EXIF_TAG_MODEL = 272
_EXIF_TAG_DATETIME_ORIGINAL = 36867
_EXIF_TAG_FNUMBER = 33437
_EXIF_TAG_EXPOSURE_TIME = 33434
_EXIF_TAG_FOCAL_LENGTH = 37386
_EXIF_TAG_LENS_MODEL = 42036


def extract_image_metadata(file):
    result = {
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
    try:
        img = Image.open(file)
        img.load()
    except Exception:
        return result
    result['width'], result['height'] = img.size
    result['format'] = img.format
    result['color_mode'] = img.mode
    icc_data = img.info.get('icc_profile')
    if icc_data:
        try:
            profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_data))
            result['icc_profile'] = ImageCms.getProfileName(profile).strip()
        except Exception:
            pass
    try:
        exif = img.getexif()
        taken_str = exif.get(_EXIF_TAG_DATETIME_ORIGINAL)
        if taken_str:
            from django.utils import timezone

            naive = datetime.strptime(taken_str, '%Y:%m:%d %H:%M:%S')
            result['taken_at'] = timezone.make_aware(naive)
        result['camera_make'] = exif.get(_EXIF_TAG_MAKE) or None
        result['camera_model'] = exif.get(_EXIF_TAG_MODEL) or None
        exif_ifd = exif.get_ifd(0x8769)
        result['lens'] = exif_ifd.get(_EXIF_TAG_LENS_MODEL) or None
        raw_aperture = exif_ifd.get(_EXIF_TAG_FNUMBER)
        if raw_aperture is not None:
            result['aperture'] = float(raw_aperture)
        raw_shutter = exif_ifd.get(_EXIF_TAG_EXPOSURE_TIME)
        if raw_shutter is not None:
            frac = Fraction(float(raw_shutter)).limit_denominator(100000)
            if frac.denominator == 1:
                result['shutter_speed'] = str(frac.numerator)
            else:
                result['shutter_speed'] = f'{frac.numerator}/{frac.denominator}'
        raw_focal = exif_ifd.get(_EXIF_TAG_FOCAL_LENGTH)
        if raw_focal is not None:
            result['focal_length'] = float(raw_focal)
    except Exception:
        pass
    return result


def upload_image_files(files):
    for f in files:
        meta = extract_image_metadata(f)
        f.seek(0)
        title = Path(f.name).stem.replace('-', ' ').replace('_', ' ').title()
        media_type, _ = mimetypes.guess_type(f.name)
        resource = Resource.objects.create(
            resource_type=Resource.Type.IMAGE,
            title=title,
            produced_at=meta['taken_at'],
        )
        MediaFile.objects.create(
            resource=resource,
            file=f,
            media_type=media_type or '',
            file_size=f.size,
            width=meta['width'],
            height=meta['height'],
        )
        exif_data = {
            k: v
            for k, v in {
                'format': meta['format'],
                'color_mode': meta['color_mode'],
                'icc_profile': meta['icc_profile'],
                'camera_make': meta['camera_make'],
                'camera_model': meta['camera_model'],
                'lens': meta['lens'],
                'aperture': meta['aperture'],
                'shutter_speed': meta['shutter_speed'],
                'focal_length': meta['focal_length'],
            }.items()
            if v is not None
        }
        if exif_data:
            Metadata.objects.create(
                resource=resource,
                type=Metadata.Type.EXIF,
                data=exif_data,
            )


def _ffprobe(path):
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v',
                'quiet',
                '-print_format',
                'json',
                '-show_streams',
                '-show_format',
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return json.loads(result.stdout)
    except Exception:
        return {}


def extract_video_metadata(file):
    result = {
        'duration': None,
        'width': None,
        'height': None,
    }
    if hasattr(file, 'temporary_file_path'):
        data = _ffprobe(file.temporary_file_path())
    else:
        suffix = Path(file.name).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
            tmp.write(file.read())
            tmp.flush()
            file.seek(0)
            data = _ffprobe(tmp.name)
    fmt = data.get('format', {})
    duration_str = fmt.get('duration')
    if duration_str:
        result['duration'] = timedelta(seconds=float(duration_str))
    for stream in data.get('streams', []):
        if stream.get('codec_type') == 'video' and result['width'] is None:
            result['width'] = stream.get('width')
            result['height'] = stream.get('height')
    return result


def upload_video_files(files):
    for f in files:
        meta = extract_video_metadata(f)
        f.seek(0)
        title = Path(f.name).stem.replace('-', ' ').replace('_', ' ').title()
        media_type, _ = mimetypes.guess_type(f.name)
        resource = Resource.objects.create(
            resource_type=Resource.Type.VIDEO,
            title=title,
        )
        MediaFile.objects.create(
            resource=resource,
            file=f,
            media_type=media_type or '',
            file_size=f.size,
            duration=meta['duration'],
            width=meta['width'],
            height=meta['height'],
        )


def upload_audio_files(files):
    for f in files:
        meta = extract_metadata(f)
        f.seek(0)
        title = (
            meta['title']
            or Path(f.name).stem.replace('-', ' ').replace('_', ' ').title()
        )
        media_type, _ = mimetypes.guess_type(f.name)
        resource = Resource.objects.create(
            resource_type=Resource.Type.AUDIO,
            title=title,
        )
        MediaFile.objects.create(
            resource=resource,
            file=f,
            media_type=media_type or '',
            file_size=f.size,
            duration=meta['duration'],
        )
