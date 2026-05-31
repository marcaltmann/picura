from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='backoffice_dashboard'),
    path('batches/', views.batch_list, name='backoffice_batch_list'),
    path('batches/<int:pk>/', views.batch_detail, name='backoffice_batch_detail'),
    path(
        'batches/<int:pk>/assign-to-album/',
        views.batch_assign_to_album,
        name='backoffice_batch_assign_to_album',
    ),
    path('photos/', views.photo_list, name='backoffice_photo_list'),
    path('photos/<int:pk>/', views.photo_detail, name='backoffice_photo_detail'),
    path('photos/upload/', views.photo_upload, name='backoffice_photo_upload'),
    path(
        'photos/bulk-delete/',
        views.photo_bulk_delete,
        name='backoffice_photo_bulk_delete',
    ),
    path('photos/<int:pk>/delete/', views.photo_delete, name='backoffice_photo_delete'),
    path('albums/', views.album_list, name='backoffice_album_list'),
    path('albums/new/', views.album_create, name='backoffice_album_create'),
    path('albums/<int:pk>/', views.album_detail, name='backoffice_album_detail'),
    path(
        'albums/<int:pk>/photos/<int:photo_pk>/set-primary/',
        views.album_set_primary,
        name='backoffice_album_set_primary',
    ),
    path('albums/<int:pk>/delete/', views.album_delete, name='backoffice_album_delete'),
]
