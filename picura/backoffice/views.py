from django.db import models
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from picura.albums.models import Album
from picura.photos.models import Batch, Metadata, Photo
from picura.photos.use_cases import upload_photos

from .forms import AlbumForm, PhotoForm


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
    return render(request, 'backoffice/batch_list.html', {'batch_list': batches})


def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    albums = Album.objects.all()
    return render(
        request, 'backoffice/batch_detail.html', {'batch': batch, 'albums': albums}
    )


def batch_assign_to_album(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        photo_ids = request.POST.getlist('photo_ids')
        album_id = request.POST.get('album_id')
        if photo_ids and album_id:
            album = get_object_or_404(Album, pk=album_id)
            photos = Photo.objects.filter(pk__in=photo_ids, batch=batch).exclude(
                albums=album
            )
            if photos.exists():
                album.append_photos(photos)
    return redirect('backoffice_batch_detail', pk=pk)


def photo_list(request):
    return render(
        request,
        'backoffice/photo_list.html',
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
        'backoffice/photo_detail.html',
        {'photo': photo, 'exif': exif, 'form': form},
    )


def photo_upload(request):
    if request.method == 'POST':
        batch = upload_photos(request.FILES.getlist('files'))
        return redirect('backoffice_batch_detail', pk=batch.pk)
    return render(request, 'backoffice/photo_upload.html')


def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        photo.delete()
        return redirect('backoffice_photo_list')
    return render(request, 'backoffice/photo_delete.html', {'photo': photo})


def photo_bulk_delete(request):
    if request.method == 'POST':
        ids = request.POST.getlist('photo_ids')
        Photo.objects.filter(pk__in=ids).delete()
    return redirect('backoffice_photo_list')


def album_list(request):
    return render(
        request,
        'backoffice/album_list.html',
        {'album_list': Album.objects.all()},
    )


def album_create(request):
    if request.method == 'POST':
        form = AlbumForm(request.POST)
        if form.is_valid():
            album = form.save()
            return redirect('backoffice_album_detail', pk=album.pk)
    else:
        form = AlbumForm()
    return render(request, 'backoffice/album_create.html', {'form': form})


def album_detail(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            return redirect('backoffice_album_detail', pk=pk)
    else:
        form = AlbumForm(instance=album)
    return render(
        request, 'backoffice/album_detail.html', {'album': album, 'form': form}
    )


def album_delete(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        album.delete()
        return redirect('backoffice_album_list')
    return render(request, 'backoffice/album_delete.html', {'album': album})
