from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Photo

PAGE_SIZE = 48


def photo_list(request):
    photos = Photo.objects.order_by('-produced_at', '-created_at')
    paginator = Paginator(photos, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'photos/photo_list.html', {'page_obj': page_obj})


def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    return render(request, 'photos/photo_detail.html', {'photo': photo})
