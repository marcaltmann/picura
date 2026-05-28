from django.urls import path

from . import views

urlpatterns = [
    path('', views.photo_list, name='photos_photo_list'),
    path('<int:pk>/', views.photo_detail, name='photos_photo_detail'),
]
