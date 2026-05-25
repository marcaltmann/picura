import mimetypes
from pathlib import Path

from .extraction import (
    extract_audio_metadata,
    extract_image_metadata,
    extract_video_metadata,
)
from .models import Metadata, Resource


def _title_from_filename(name):
    return Path(name).stem.replace('-', ' ').replace('_', ' ').title()


def upload_image_files(files):
    for f in files:
        meta = extract_image_metadata(f)
        f.seek(0)
        media_type, _ = mimetypes.guess_type(f.name)
        resource = Resource.objects.create(
            resource_type=Resource.Type.IMAGE,
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
                resource=resource,
                type=Metadata.Type.EXIF,
                data=exif_data,
            )


def upload_video_files(files):
    for f in files:
        meta = extract_video_metadata(f)
        f.seek(0)
        media_type, _ = mimetypes.guess_type(f.name)
        Resource.objects.create(
            resource_type=Resource.Type.VIDEO,
            title=_title_from_filename(f.name),
            file=f,
            media_type=media_type or '',
            file_size=f.size,
            duration=meta['duration'],
            width=meta['width'],
            height=meta['height'],
        )


def upload_audio_files(files):
    for f in files:
        meta = extract_audio_metadata(f)
        f.seek(0)
        media_type, _ = mimetypes.guess_type(f.name)
        Resource.objects.create(
            resource_type=Resource.Type.AUDIO,
            title=meta['title'] or _title_from_filename(f.name),
            file=f,
            media_type=media_type or '',
            file_size=f.size,
            duration=meta['duration'],
        )
