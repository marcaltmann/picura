from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from curio.photos.models import Metadata, Photo
from curio.photos.use_cases import upload_photos

from .forms import PhotoForm


def dashboard(request):
    photo_count = Photo.objects.count()
    total_file_size = (
        Photo.objects.aggregate(total=models.Sum('file_size'))['total'] or 0
    )
    return render(
        request,
        'backoffice/dashboard.html',
        {
            'photo_count': photo_count,
            'total_file_size': total_file_size,
        },
    )


def photo_list(request):
    return render(
        request,
        'backoffice/content/photo_list.html',
        {
            'photo_list': Photo.objects.order_by('-created_at'),
        },
    )


def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        form = PhotoForm(request.POST, instance=photo)
        if form.is_valid():
            form.save()
            return redirect('backoffice_photo_detail', pk=pk)
    else:
        form = PhotoForm(instance=photo)
    exif = photo.metadata.filter(type=Metadata.Type.EXIF).first()
    return render(
        request,
        'backoffice/content/photo_detail.html',
        {'photo': photo, 'exif': exif, 'form': form},
    )


def photo_upload(request):
    if request.method == 'POST':
        upload_photos(request.FILES.getlist('files'))
        return redirect('backoffice_photo_list')
    return render(request, 'backoffice/content/photo_upload.html')


def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        photo.delete()
        return redirect('backoffice_photo_list')
    return render(request, 'backoffice/content/photo_delete.html', {'photo': photo})


def photo_bulk_delete(request):
    if request.method == 'POST':
        ids = request.POST.getlist('photo_ids')
        Photo.objects.filter(pk__in=ids).delete()
    return redirect('backoffice_photo_list')
