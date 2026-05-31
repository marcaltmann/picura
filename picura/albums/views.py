from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Album

PAGE_SIZE = 48


def album_list(request):
    albums = Album.objects.with_date_range().with_primary_photo()
    paginator = Paginator(albums, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'albums/album_list.html', {'page_obj': page_obj})


def album_detail(request, pk):
    album = get_object_or_404(Album, pk=pk)
    photos = album.photos.order_by('album_links__position')
    return render(
        request, 'albums/album_detail.html', {'album': album, 'photos': photos}
    )


def album_photo_detail(request, album_pk, photo_pk):
    album = get_object_or_404(Album, pk=album_pk)
    link = get_object_or_404(
        album.photo_links.select_related('photo'), photo_id=photo_pk
    )
    photo = link.photo

    # Positions run 1..N with no gaps, so neighbours are position ± 1.
    # A missing position (0 at the start, N + 1 at the end) simply yields no link.
    neighbours = dict(
        album.photo_links.filter(
            position__in=(link.position - 1, link.position + 1)
        ).values_list('position', 'photo_id')
    )

    def url_for(position):
        if position not in neighbours:
            return None
        return reverse('albums_photo_detail', args=[album_pk, neighbours[position]])

    prev_url = url_for(link.position - 1)
    next_url = url_for(link.position + 1)

    return render(
        request,
        'photos/photo_detail.html',
        {'photo': photo, 'album': album, 'prev_url': prev_url, 'next_url': next_url},
    )
