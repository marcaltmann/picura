import pytest
from PIL import Image

from picura.photos.models import Photo


@pytest.fixture
def make_photo(settings):
    img_dir = settings.MEDIA_ROOT / 'photos'
    img_dir.mkdir(parents=True, exist_ok=True)
    counter = [0]

    def _make(batch=None, **kwargs):
        counter[0] += 1
        name = f'test_{counter[0]}.jpg'
        img = Image.new('RGB', (10, 10), color='red')
        img.save(img_dir / name, 'JPEG')
        return Photo.objects.create(
            title=kwargs.get('title', f'Photo {counter[0]}'),
            file=f'photos/{name}',
            batch=batch,
        )

    return _make


@pytest.fixture
def photo(make_photo):
    return make_photo(title='Test Photo')
