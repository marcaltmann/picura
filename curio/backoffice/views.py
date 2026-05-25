from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from curio.resources.models import Metadata, Resource
from curio.resources.use_cases import (
    upload_audio_files,
    upload_image_files,
    upload_video_files,
)

from .forms import ResourceForm


def dashboard(request):
    counts = Resource.objects.values('resource_type').annotate(
        count=models.Count('id'), size=models.Sum('file_size')
    )
    count_map = {row['resource_type']: row for row in counts}

    def _count(t):
        return count_map.get(t, {}).get('count', 0)

    def _size(t):
        return count_map.get(t, {}).get('size', 0) or 0

    return render(
        request,
        'backoffice/dashboard.html',
        {
            'image_count': _count(Resource.Type.IMAGE),
            'audio_count': _count(Resource.Type.AUDIO),
            'video_count': _count(Resource.Type.VIDEO),
            'document_count': _count(Resource.Type.DOCUMENT),
            'total_file_size': sum(_size(t) for t in Resource.Type),
        },
    )


def audio_list(request):
    return render(
        request,
        'backoffice/content/audio_list.html',
        {
            'audio_list': Resource.objects.filter(
                resource_type=Resource.Type.AUDIO
            ).order_by('-created_at'),
        },
    )


def audio_detail(request, pk):
    audio = get_object_or_404(Resource, pk=pk, resource_type=Resource.Type.AUDIO)
    return render(request, 'backoffice/content/audio_detail.html', {'audio': audio})


def audio_upload(request):
    if request.method == 'POST':
        upload_audio_files(request.FILES.getlist('files'))
        return redirect('backoffice_audio_list')
    return render(request, 'backoffice/content/audio_upload.html')


def image_list(request):
    return render(
        request,
        'backoffice/content/image_list.html',
        {
            'image_list': Resource.objects.filter(
                resource_type=Resource.Type.IMAGE
            ).order_by('-created_at'),
        },
    )


def image_detail(request, pk):
    image = get_object_or_404(Resource, pk=pk, resource_type=Resource.Type.IMAGE)
    if request.method == 'POST':
        form = ResourceForm(request.POST, instance=image)
        if form.is_valid():
            form.save()
            return redirect('backoffice_image_detail', pk=pk)
    else:
        form = ResourceForm(instance=image)
    exif = image.metadata.filter(type=Metadata.Type.EXIF).first()
    return render(
        request,
        'backoffice/content/image_detail.html',
        {'image': image, 'exif': exif, 'form': form},
    )


def image_upload(request):
    if request.method == 'POST':
        upload_image_files(request.FILES.getlist('files'))
        return redirect('backoffice_image_list')
    return render(request, 'backoffice/content/image_upload.html')


def video_list(request):
    return render(
        request,
        'backoffice/content/video_list.html',
        {
            'video_list': Resource.objects.filter(
                resource_type=Resource.Type.VIDEO
            ).order_by('-created_at'),
        },
    )


def video_detail(request, pk):
    video = get_object_or_404(Resource, pk=pk, resource_type=Resource.Type.VIDEO)
    return render(request, 'backoffice/content/video_detail.html', {'video': video})


def video_upload(request):
    if request.method == 'POST':
        upload_video_files(request.FILES.getlist('files'))
        return redirect('backoffice_video_list')
    return render(request, 'backoffice/content/video_upload.html')


def audio_delete(request, pk):
    audio = get_object_or_404(Resource, pk=pk, resource_type=Resource.Type.AUDIO)
    if request.method == 'POST':
        audio.delete()
        return redirect('backoffice_audio_list')
    return render(request, 'backoffice/content/audio_delete.html', {'audio': audio})


def image_delete(request, pk):
    image = get_object_or_404(Resource, pk=pk, resource_type=Resource.Type.IMAGE)
    if request.method == 'POST':
        image.delete()
        return redirect('backoffice_image_list')
    return render(request, 'backoffice/content/image_delete.html', {'image': image})


def video_delete(request, pk):
    video = get_object_or_404(Resource, pk=pk, resource_type=Resource.Type.VIDEO)
    if request.method == 'POST':
        video.delete()
        return redirect('backoffice_video_list')
    return render(request, 'backoffice/content/video_delete.html', {'video': video})
