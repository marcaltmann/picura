from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from picura.photos.models import Photo

from .models import Album

PAGE_SIZE = 48


def album_list(request):
    albums = Album.objects.all()
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
    photo = get_object_or_404(Photo, pk=photo_pk, albums=album)

    photo_ids = list(
        album.photo_links.order_by('position').values_list('photo_id', flat=True)
    )
    idx = photo_ids.index(photo_pk)

    prev_url = (
        reverse('albums_photo_detail', args=[album_pk, photo_ids[idx - 1]])
        if idx > 0
        else None
    )
    next_url = (
        reverse('albums_photo_detail', args=[album_pk, photo_ids[idx + 1]])
        if idx < len(photo_ids) - 1
        else None
    )

    return render(
        request,
        'photos/photo_detail.html',
        {'photo': photo, 'album': album, 'prev_url': prev_url, 'next_url': next_url},
    )
