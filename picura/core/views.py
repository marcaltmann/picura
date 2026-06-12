from django.shortcuts import render
from django.views.decorators.http import require_GET

from picura.albums.models import Album


@require_GET
def welcome(request):
    recent_albums = (
        Album.objects.public().with_primary_photo().order_by('-created_at')[:5]
    )
    return render(request, 'core/welcome.html', {'recent_albums': recent_albums})
