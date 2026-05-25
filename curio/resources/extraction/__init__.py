import io
import json
import subprocess
import tempfile
from datetime import timedelta
from pathlib import Path

import mutagen
from PIL import Image, ImageCms

from .exif import extract_exif
from .iptc import extract_iptc


def _extract_icc_profile(img):
    icc_data = img.info.get('icc_profile')
    if not icc_data:
        return None
    try:
        profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_data))
        return ImageCms.getProfileName(profile).strip()
    except Exception:
        return None


def extract_audio_metadata(file):
    result = {'title': None, 'duration': None}
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


def extract_image_metadata(file):
    result = {
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
    }
    try:
        img = Image.open(file)
        img.load()
    except Exception:
        return result
    result['width'], result['height'] = img.size
    result['format'] = img.format
    result['color_mode'] = img.mode
    iptc = extract_iptc(img)
    result['title'] = iptc.title
    result['description'] = iptc.description
    result['icc_profile'] = _extract_icc_profile(img)
    exif = extract_exif(img)
    result['taken_at'] = exif.taken_at
    result['camera_make'] = exif.camera_make
    result['camera_model'] = exif.camera_model
    result['lens'] = exif.lens
    result['aperture'] = exif.aperture
    result['shutter_speed'] = exif.shutter_speed
    result['focal_length'] = exif.focal_length
    return result


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
    result = {'duration': None, 'width': None, 'height': None}
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
