import pytest
from django.utils import timezone

from picura.albums.models import Album


@pytest.fixture
def draft_album(db):
    return Album.objects.create(name='Draft Album')


@pytest.fixture
def published_album(db):
    album = Album.objects.create(name='Published Album')
    album.publish()
    album.save()
    return album


# --- default state ---


@pytest.mark.django_db
def test_new_album_is_draft(draft_album):
    assert draft_album.status == Album.Status.DRAFT


@pytest.mark.django_db
def test_new_album_has_no_published_at(draft_album):
    assert draft_album.published_at is None


# --- publish() ---


@pytest.mark.django_db
def test_publish_sets_status_to_published(draft_album):
    draft_album.publish()
    assert draft_album.status == Album.Status.PUBLISHED


@pytest.mark.django_db
def test_publish_sets_published_at(draft_album):
    before = timezone.now()
    draft_album.publish()
    assert draft_album.published_at >= before


@pytest.mark.django_db
def test_publish_persists_to_database(draft_album):
    draft_album.publish()
    draft_album.save()
    reloaded = Album.objects.get(pk=draft_album.pk)
    assert reloaded.status == Album.Status.PUBLISHED
    assert reloaded.published_at is not None


@pytest.mark.django_db
def test_publish_does_not_overwrite_existing_published_at(published_album):
    original_ts = published_album.published_at
    published_album.publish()
    assert published_album.published_at == original_ts


# --- is_published property ---


@pytest.mark.django_db
def test_is_published_false_for_draft(draft_album):
    assert draft_album.is_published is False


@pytest.mark.django_db
def test_is_published_true_for_published(published_album):
    assert published_album.is_published is True


# --- manager filtering ---


@pytest.mark.django_db
def test_published_queryset_excludes_drafts(draft_album, published_album):
    pks = Album.objects.published().values_list('pk', flat=True)
    assert published_album.pk in pks
    assert draft_album.pk not in pks


@pytest.mark.django_db
def test_draft_queryset_excludes_published(draft_album, published_album):
    pks = Album.objects.drafts().values_list('pk', flat=True)
    assert draft_album.pk in pks
    assert published_album.pk not in pks
