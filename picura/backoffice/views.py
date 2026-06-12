from django.db import models
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render

from picura.albums.models import Album
from picura.photos.models import Batch, Metadata, Photo
from picura.photos.use_cases import upload_photos

from .decorators import staff_required
from .forms import AlbumCreateForm, AlbumForm, PhotoForm


@staff_required
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


@staff_required
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


@staff_required
def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    photos = batch.photos.order_by(
        F('produced_at').asc(nulls_last=True), 'pk'
    ).prefetch_related('albums')
    albums = Album.objects.all()
    return render(
        request,
        'backoffice/batch_detail.html',
        {'batch': batch, 'photos': photos, 'albums': albums},
    )


@staff_required
def batch_assign_to_album(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        photo_ids = request.POST.getlist('photo_ids')
        album_id = request.POST.get('album_id')
        if photo_ids and album_id:
            album = get_object_or_404(Album, pk=album_id)
            photos = (
                Photo.objects.filter(pk__in=photo_ids, batch=batch)
                .exclude(albums=album)
                .order_by(F('produced_at').asc(nulls_last=True), 'pk')
            )
            if photos.exists():
                album.append_photos(photos)
    return redirect('backoffice_batch_detail', pk=pk)


@staff_required
def photo_list(request):
    return render(
        request,
        'backoffice/photo_list.html',
        {
            'photo_list': Photo.objects.order_by('-created_at'),
        },
    )


@staff_required
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


@staff_required
def photo_upload(request):
    if request.method == 'POST':
        batch = upload_photos(request.FILES.getlist('files'))
        return redirect('backoffice_batch_detail', pk=batch.pk)
    return render(request, 'backoffice/photo_upload.html')


@staff_required
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        photo.delete()
        return redirect('backoffice_photo_list')
    return render(request, 'backoffice/photo_delete.html', {'photo': photo})


@staff_required
def photo_bulk_delete(request):
    if request.method == 'POST':
        ids = request.POST.getlist('photo_ids')
        Photo.objects.filter(pk__in=ids).delete()
    return redirect('backoffice_photo_list')


@staff_required
def album_list(request):
    return render(
        request,
        'backoffice/album_list.html',
        {'album_list': Album.objects.all()},
    )


@staff_required
def album_create(request):
    if request.method == 'POST':
        form = AlbumCreateForm(request.POST)
        if form.is_valid():
            album = form.save()
            return redirect('backoffice_album_detail', pk=album.pk)
    else:
        form = AlbumCreateForm()
    return render(request, 'backoffice/album_create.html', {'form': form})


@staff_required
def album_detail(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            return redirect('backoffice_album_detail', pk=pk)
    else:
        form = AlbumForm(instance=album)
    photo_links = album.photo_links.select_related('photo').order_by('position')
    return render(
        request,
        'backoffice/album_detail.html',
        {'album': album, 'form': form, 'photo_links': photo_links},
    )


@staff_required
def album_set_primary(request, pk, photo_pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        photo = get_object_or_404(album.photos, pk=photo_pk)
        album.set_primary(photo)
    return redirect('backoffice_album_detail', pk=pk)


@staff_required
def album_remove_photo(request, pk, photo_pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        photo = get_object_or_404(album.photos, pk=photo_pk)
        album.remove_photos(photo)
    return redirect('backoffice_album_detail', pk=pk)


@staff_required
def album_delete(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        album.delete()
        return redirect('backoffice_album_list')
    return render(request, 'backoffice/album_delete.html', {'album': album})
