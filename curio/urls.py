from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

import curio.core.views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('backoffice/', include('curio.backoffice.urls')),
    path('accounts/', include('allauth.urls')),
    path('', core_views.welcome, name='welcome'),
]

if settings.DJANGO_ENV == 'development':
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
