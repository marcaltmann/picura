from datetime import UTC, datetime

import pytest
from django.urls import reverse

from picura.albums.models import Album, AlbumPhoto
from picura.photos.models import Batch


@pytest.mark.django_db
def test_batch_list_returns_200(client):
    response = client.get(reverse('backoffice_batch_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_batch_list_context_contains_batches(client):
    batch = Batch.objects.create()
    response = client.get(reverse('backoffice_batch_list'))
    assert batch in response.context['batch_list']


@pytest.mark.django_db
def test_batch_list_annotates_photo_count(client, make_photo):
    batch = Batch.objects.create()
    make_photo(batch=batch)
    make_photo(batch=batch)
    response = client.get(reverse('backoffice_batch_list'))
    assert response.context['batch_list'][0].photo_count == 2


@pytest.mark.django_db
def test_batch_list_annotates_assigned_count_zero_when_unassigned(client, make_photo):
    batch = Batch.objects.create()
    make_photo(batch=batch)
    response = client.get(reverse('backoffice_batch_list'))
    assert response.context['batch_list'][0].assigned_count == 0


@pytest.mark.django_db
def test_batch_list_annotates_assigned_count_when_some_assigned(client, make_photo):
    batch = Batch.objects.create()
    p1 = make_photo(batch=batch)
    make_photo(batch=batch)
    album = Album.objects.create(name='Test Album')
    AlbumPhoto.objects.create(album=album, photo=p1, position=1)
    response = client.get(reverse('backoffice_batch_list'))
    assert response.context['batch_list'][0].assigned_count == 1


@pytest.mark.django_db
def test_batch_detail_returns_200(client):
    batch = Batch.objects.create()
    response = client.get(reverse('backoffice_batch_detail', args=[batch.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_batch_detail_returns_404_for_missing(client):
    response = client.get(reverse('backoffice_batch_detail', args=[9999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_batch_detail_context_contains_batch(client):
    batch = Batch.objects.create()
    response = client.get(reverse('backoffice_batch_detail', args=[batch.pk]))
    assert response.context['batch'] == batch


@pytest.mark.django_db
def test_batch_detail_context_contains_albums(client):
    batch = Batch.objects.create()
    album = Album.objects.create(name='Summer 2024')
    response = client.get(reverse('backoffice_batch_detail', args=[batch.pk]))
    assert album in response.context['albums']


@pytest.mark.django_db
def test_batch_detail_photos_ordered_by_produced_at(client, make_photo):
    batch = Batch.objects.create()
    later = make_photo(batch=batch, produced_at=datetime(2026, 5, 2, tzinfo=UTC))
    earlier = make_photo(batch=batch, produced_at=datetime(2026, 5, 1, tzinfo=UTC))
    response = client.get(reverse('backoffice_batch_detail', args=[batch.pk]))
    assert list(response.context['photos']) == [earlier, later]


@pytest.mark.django_db
def test_batch_detail_photos_without_produced_at_come_last(client, make_photo):
    batch = Batch.objects.create()
    undated = make_photo(batch=batch)
    dated = make_photo(batch=batch, produced_at=datetime(2026, 5, 1, tzinfo=UTC))
    response = client.get(reverse('backoffice_batch_detail', args=[batch.pk]))
    assert list(response.context['photos']) == [dated, undated]


@pytest.mark.django_db
def test_batch_assign_to_album_post_appends_photos(client, make_photo):
    batch = Batch.objects.create()
    p1 = make_photo(batch=batch)
    p2 = make_photo(batch=batch)
    album = Album.objects.create(name='Summer 2024')
    client.post(
        reverse('backoffice_batch_assign_to_album', args=[batch.pk]),
        {'photo_ids': [p1.pk, p2.pk], 'album_id': album.pk},
    )
    assert album.photos.count() == 2
    assert p1 in album.photos.all()
    assert p2 in album.photos.all()


@pytest.mark.django_db
def test_batch_assign_to_album_appends_in_produced_at_order(client, make_photo):
    batch = Batch.objects.create()
    later = make_photo(batch=batch, produced_at=datetime(2026, 5, 2, tzinfo=UTC))
    earlier = make_photo(batch=batch, produced_at=datetime(2026, 5, 1, tzinfo=UTC))
    album = Album.objects.create(name='Summer 2024')
    client.post(
        reverse('backoffice_batch_assign_to_album', args=[batch.pk]),
        {'photo_ids': [later.pk, earlier.pk], 'album_id': album.pk},
    )
    assert album.photo_at(1) == earlier
    assert album.photo_at(2) == later


@pytest.mark.django_db
def test_batch_assign_to_album_post_redirects_to_batch_detail(client, make_photo):
    batch = Batch.objects.create()
    p = make_photo(batch=batch)
    album = Album.objects.create(name='Summer 2024')
    response = client.post(
        reverse('backoffice_batch_assign_to_album', args=[batch.pk]),
        {'photo_ids': [p.pk], 'album_id': album.pk},
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('backoffice_batch_detail', args=[batch.pk])


@pytest.mark.django_db
def test_batch_assign_to_album_post_skips_already_assigned(client, make_photo):
    batch = Batch.objects.create()
    p = make_photo(batch=batch)
    album = Album.objects.create(name='Summer 2024')
    album.append_photos(p)
    response = client.post(
        reverse('backoffice_batch_assign_to_album', args=[batch.pk]),
        {'photo_ids': [p.pk], 'album_id': album.pk},
    )
    assert response.status_code == 302
    assert album.photos.count() == 1


@pytest.mark.django_db
def test_batch_assign_to_album_post_with_no_ids_redirects(client):
    batch = Batch.objects.create()
    album = Album.objects.create(name='Summer 2024')
    response = client.post(
        reverse('backoffice_batch_assign_to_album', args=[batch.pk]),
        {'album_id': album.pk},
    )
    assert response.status_code == 302
    assert album.photos.count() == 0


@pytest.mark.django_db
def test_batch_assign_to_album_post_invalid_album_returns_404(client, make_photo):
    batch = Batch.objects.create()
    p = make_photo(batch=batch)
    response = client.post(
        reverse('backoffice_batch_assign_to_album', args=[batch.pk]),
        {'photo_ids': [p.pk], 'album_id': 9999},
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_batch_assign_to_album_get_redirects(client):
    batch = Batch.objects.create()
    response = client.get(reverse('backoffice_batch_assign_to_album', args=[batch.pk]))
    assert response.status_code == 302
