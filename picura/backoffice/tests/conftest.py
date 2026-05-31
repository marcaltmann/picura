import pytest
from django.contrib.auth import get_user_model
from PIL import Image

from picura.photos.models import Photo


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username='staff', password='pw', is_staff=True
    )


@pytest.fixture
def non_staff_user(db):
    return get_user_model().objects.create_user(
        username='member', password='pw', is_staff=False
    )


@pytest.fixture(autouse=True)
def _login_staff(client, staff_user):
    # The backoffice is staff-only. The existing tests exercise behaviour, not
    # access control, so log the default test client in as staff. The
    # access-control tests in test_access_control.py use their own clients.
    client.force_login(staff_user)


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
