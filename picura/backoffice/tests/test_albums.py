import pytest
from django.urls import reverse

from picura.albums.models import Album, AlbumPhoto


@pytest.mark.django_db
def test_album_list_returns_200(client):
    response = client.get(reverse('backoffice_album_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_list_context_contains_albums(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_list'))
    assert album in response.context['album_list']


@pytest.mark.django_db
def test_album_list_shows_album_name(client):
    Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_list'))
    assert b'Summer 2024' in response.content


@pytest.mark.django_db
def test_album_create_get_returns_200(client):
    response = client.get(reverse('backoffice_album_create'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_create_post_creates_album_and_redirects(client):
    response = client.post(reverse('backoffice_album_create'), {'name': 'New Album'})
    assert response.status_code == 302
    album = Album.objects.get(name='New Album')
    assert response['Location'] == reverse('backoffice_album_detail', args=[album.pk])


@pytest.mark.django_db
def test_album_create_post_invalid_rerenders(client):
    response = client.post(reverse('backoffice_album_create'), {'name': ''})
    assert response.status_code == 200
    assert Album.objects.count() == 0


@pytest.mark.django_db
def test_album_detail_returns_200(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_detail_context_contains_album(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert response.context['album'] == album


@pytest.mark.django_db
def test_album_detail_shows_album_name(client):
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert b'Summer 2024' in response.content


@pytest.mark.django_db
def test_album_detail_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_album_detail', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_album_detail_links_to_public_album_when_published(client):
    album = Album.objects.create(name='Summer 2024', status=Album.Status.PUBLISHED)
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert f'href="{album.get_absolute_url()}"'.encode() in response.content


@pytest.mark.django_db
def test_album_detail_hides_public_link_for_draft(client):
    album = Album.objects.create(name='Summer 2024', status=Album.Status.DRAFT)
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert f'href="{album.get_absolute_url()}"'.encode() not in response.content


@pytest.mark.django_db
def test_album_detail_shows_photos_in_position_order(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    p1 = make_photo(title='First')
    p2 = make_photo(title='Second')
    AlbumPhoto.objects.create(album=album, photo=p2, position=2)
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    content = response.content.decode()
    assert content.index('First') < content.index('Second')


@pytest.mark.django_db
def test_album_detail_marks_primary_photo(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    p1 = make_photo(title='Primary One')
    album.append_photos(p1)
    response = client.get(reverse('backoffice_album_detail', args=[album.pk]))
    assert b'Primary' in response.content


@pytest.mark.django_db
def test_album_detail_post_updates_name_and_redirects(client):
    album = Album.objects.create(name='Old Name')
    response = client.post(
        reverse('backoffice_album_detail', args=[album.pk]),
        {'name': 'New Name'},
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_album_detail', args=[album.pk])
    album.refresh_from_db()
    assert album.name == 'New Name'


@pytest.mark.django_db
def test_album_detail_post_invalid_rerenders(client):
    album = Album.objects.create(name='Old Name')
    response = client.post(
        reverse('backoffice_album_detail', args=[album.pk]),
        {'name': ''},
    )
    assert response.status_code == 200
    album.refresh_from_db()
    assert album.name == 'Old Name'


@pytest.mark.django_db
def test_album_set_primary_post_moves_photo_to_position_one(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    p1 = make_photo(title='First')
    p2 = make_photo(title='Second')
    album.append_photos([p1, p2])
    response = client.post(
        reverse('backoffice_album_set_primary', args=[album.pk, p2.pk])
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_album_detail', args=[album.pk])
    assert album.photo_links.get(photo=p2).position == 1
    assert album.photo_links.get(photo=p1).position == 2


@pytest.mark.django_db
def test_album_set_primary_404_for_photo_not_in_album(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    other = make_photo(title='Outsider')
    response = client.post(
        reverse('backoffice_album_set_primary', args=[album.pk, other.pk])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_album_set_primary_get_redirects(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    p1 = make_photo(title='First')
    album.append_photos(p1)
    response = client.get(
        reverse('backoffice_album_set_primary', args=[album.pk, p1.pk])
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_album_remove_photo_post_removes_and_renumbers(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    p1 = make_photo(title='First')
    p2 = make_photo(title='Second')
    p3 = make_photo(title='Third')
    album.append_photos([p1, p2, p3])
    response = client.post(
        reverse('backoffice_album_remove_photo', args=[album.pk, p1.pk])
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_album_detail', args=[album.pk])
    assert not album.photo_links.filter(photo=p1).exists()
    assert album.photo_links.get(photo=p2).position == 1
    assert album.photo_links.get(photo=p3).position == 2


@pytest.mark.django_db
def test_album_remove_photo_404_for_photo_not_in_album(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    other = make_photo(title='Outsider')
    response = client.post(
        reverse('backoffice_album_remove_photo', args=[album.pk, other.pk])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_album_remove_photo_get_redirects(client, make_photo):
    album = Album.objects.create(name='Summer 2024')
    p1 = make_photo(title='First')
    album.append_photos(p1)
    response = client.get(
        reverse('backoffice_album_remove_photo', args=[album.pk, p1.pk])
    )
    assert response.status_code == 302
    assert album.photo_links.filter(photo=p1).exists()


@pytest.mark.django_db
def test_album_delete_get_returns_200(client):
    album = Album.objects.create(name='To Delete')
    response = client.get(reverse('backoffice_album_delete', args=[album.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_album_delete_get_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_album_delete', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_album_delete_post_deletes_and_redirects(client):
    album = Album.objects.create(name='To Delete')
    response = client.post(reverse('backoffice_album_delete', args=[album.pk]))
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_album_list')
    assert not Album.objects.filter(pk=album.pk).exists()
