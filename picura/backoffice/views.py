from django.db import models
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from picura.photos.models import Batch, Metadata, Photo
from picura.photos.use_cases import upload_photos

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


def batch_list(request):
    batches = (
        Batch.objects.annotate(
            photo_count=Count('photos', distinct=True),
            assigned_count=Count(
                'photos',
                filter=Q(photos__album_links__isnull=False),
                distinct=True,
            ),
        )
        .prefetch_related('photos')
        .order_by('-created_at')
    )
    return render(
        request, 'backoffice/content/batch_list.html', {'batch_list': batches}
    )


def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    return render(request, 'backoffice/content/batch_detail.html', {'batch': batch})


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
        batch = upload_photos(request.FILES.getlist('files'))
        return redirect('backoffice_batch_detail', pk=batch.pk)
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
