import mimetypes
from pathlib import Path

from .extraction import extract_image_metadata
from .models import Metadata, Photo


def _title_from_filename(name):
    return Path(name).stem.replace('-', ' ').replace('_', ' ').title()


def upload_photos(files):
    for f in files:
        meta = extract_image_metadata(f)
        f.seek(0)
        media_type, _ = mimetypes.guess_type(f.name)
        photo = Photo.objects.create(
            title=meta['title'] or _title_from_filename(f.name),
            description=meta['description'] or '',
            file=f,
            media_type=media_type or '',
            file_size=f.size,
            width=meta['width'],
            height=meta['height'],
            produced_at=meta['taken_at'],
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
                photo=photo,
                type=Metadata.Type.EXIF,
                data=exif_data,
            )
