from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='backoffice_dashboard'),
    path('batches/', views.batch_list, name='backoffice_batch_list'),
    path('batches/<int:pk>/', views.batch_detail, name='backoffice_batch_detail'),
    path('content/photos/', views.photo_list, name='backoffice_photo_list'),
    path(
        'content/photos/<int:pk>/', views.photo_detail, name='backoffice_photo_detail'
    ),
    path('content/photos/upload/', views.photo_upload, name='backoffice_photo_upload'),
    path(
        'content/photos/bulk-delete/',
        views.photo_bulk_delete,
        name='backoffice_photo_bulk_delete',
    ),
    path(
        'content/photos/<int:pk>/delete/',
        views.photo_delete,
        name='backoffice_photo_delete',
    ),
]
