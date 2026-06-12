from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Album

PAGE_SIZE = 48


def album_list(request):
    albums = (
        Album.objects.public()
        .with_date_range()
        .with_primary_photo()
        # annotate() with aggregates drops Meta.ordering; restore it for
        # stable pagination.
        .order_by('-created_at')
    )
    paginator = Paginator(albums, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'albums/album_list.html', {'page_obj': page_obj})


def album_detail(request, pk):
    album = get_object_or_404(Album.objects.public(), pk=pk)
    photos = album.photos.order_by('album_links__position')
    return render(
        request, 'albums/album_detail.html', {'album': album, 'photos': photos}
    )


def album_photo_detail(request, album_pk, photo_pk):
    album = get_object_or_404(Album.objects.public(), pk=album_pk)
    link = get_object_or_404(
        album.photo_links.select_related('photo'), photo_id=photo_pk
    )
    photo = link.photo

    prev_id, next_id = album.neighbour_photo_ids(link.position)

    def url_for(photo_id):
        if photo_id is None:
            return None
        return reverse('albums_photo_detail', args=[album_pk, photo_id])

    prev_url = url_for(prev_id)
    next_url = url_for(next_id)

    return render(
        request,
        'photos/photo_detail.html',
        {'photo': photo, 'album': album, 'prev_url': prev_url, 'next_url': next_url},
    )
