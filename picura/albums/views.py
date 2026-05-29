from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

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
