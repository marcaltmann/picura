import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Photo


def make_public_album(name='Album', **kwargs):
    album = Album.objects.create(name=name, status=Album.Status.PUBLISHED, **kwargs)
    photo = Photo.objects.create(title='Photo')
    AlbumPhoto.objects.create(album=album, photo=photo, position=1)
    return album


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username='alice', password='pw')


@pytest.mark.django_db
def test_header_shows_sign_in_link_when_anonymous(client):
    response = client.get(reverse('welcome'))
    assert reverse('account_login').encode() in response.content


@pytest.mark.django_db
def test_header_shows_sign_out_when_authenticated(client, user):
    client.force_login(user)
    response = client.get(reverse('welcome'))
    assert reverse('account_logout').encode() in response.content
    assert b'alice' in response.content


@pytest.mark.django_db
def test_welcome_shows_recent_public_albums(client):
    albums = [make_public_album(name=f'Album {i}') for i in range(6)]
    response = client.get(reverse('welcome'))
    assert response.status_code == 200
    # Only the 5 most recent should appear
    assert b'Album 5' in response.content
    assert b'Album 1' in response.content
    assert b'Album 0' not in response.content


@pytest.mark.django_db
def test_welcome_excludes_draft_albums(client):
    Album.objects.create(name='Draft Album', status=Album.Status.DRAFT)
    response = client.get(reverse('welcome'))
    assert b'Draft Album' not in response.content


@pytest.mark.django_db
def test_welcome_excludes_empty_published_albums(client):
    Album.objects.create(name='Empty Album', status=Album.Status.PUBLISHED)
    response = client.get(reverse('welcome'))
    assert b'Empty Album' not in response.content


@pytest.mark.django_db
def test_welcome_shows_link_to_all_albums(client):
    response = client.get(reverse('welcome'))
    assert reverse('albums_album_list').encode() in response.content


@pytest.mark.django_db
def test_login_page_uses_project_layout(client):
    response = client.get(reverse('account_login'))
    assert response.status_code == 200
    # The allauth layout override pulls in the project header.
    assert b'class="header"' in response.content


@pytest.mark.django_db
def test_signup_page_renders(client):
    response = client.get(reverse('account_signup'))
    assert response.status_code == 200
    assert b'class="header"' in response.content
