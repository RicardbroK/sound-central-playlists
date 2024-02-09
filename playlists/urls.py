from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.home),
    path('view', views.view_playlist),
    path('', views.user_playlists),
    path('saved/', views.saved_playlists)
]
