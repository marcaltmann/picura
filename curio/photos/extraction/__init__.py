import io

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
        'latitude': None,
        'longitude': None,
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
    result['latitude'] = exif.latitude
    result['longitude'] = exif.longitude
    return result
