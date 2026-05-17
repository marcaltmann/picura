from django.shortcuts import get_object_or_404, render

from .models import Resource


def resource_detail(request, pk):
    resource = get_object_or_404(Resource.objects.prefetch_related('files'), pk=pk)
    return render(request, 'resources/resource_detail.html', {'resource': resource})
