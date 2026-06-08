import mimetypes
from pathlib import Path

from .extraction import extract_image_metadata
from .models import Metadata, Photo, PhotoExif, Batch


def _title_from_filename(name):
    return Path(name).stem.replace('-', ' ').replace('_', ' ').title()


def upload_photos(files) -> Batch:
    batch = Batch.objects.create()
    for f in files:
        meta = extract_image_metadata(f)
        f.seek(0)
        media_type, _ = mimetypes.guess_type(f.name)
        photo = Photo.objects.create(
            batch=batch,
            title=meta['title'] or _title_from_filename(f.name),
            description=meta['description'] or '',
            file=f,
            media_type=media_type or '',
            file_size=f.size,
            width=meta['width'],
            height=meta['height'],
            produced_at=meta['taken_at'],
        )
        if meta['raw']:
            PhotoExif.objects.create(
                photo=photo,
                camera_make=meta['camera_make'] or '',
                camera_model=meta['camera_model'] or '',
                lens=meta['lens'] or '',
                aperture=meta['aperture'],
                exposure_time=meta['exposure_time'],
                focal_length=meta['focal_length'],
                iso=meta['iso'],
                latitude=meta['latitude'],
                longitude=meta['longitude'],
                raw=meta['raw'],
            )
        dc_data = {
            k: v
            for k, v in {
                'creator': meta['creator'],
                'copyright': meta['copyright'],
                'keywords': meta['keywords'] or None,
            }.items()
            if v
        }
        if dc_data:
            Metadata.objects.create(
                photo=photo,
                type=Metadata.Type.DUBLIN_CORE,
                data=dc_data,
            )
    return batch
