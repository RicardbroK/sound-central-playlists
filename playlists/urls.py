from django.urls import path
from .views import home, apple_music_playlist_info
from . import views

urlpatterns = [
    path('create/', home.as_view(), name='create'),
    path('view/<int:playlist_id>', views.view_playlist, name='view'),
    path('view/save', views.save_playlist),
    path('', views.user_playlists),
    path('saved/', views.saved_playlists),
    path('apple/', views.apple_music_playlist_info, name='apple_playlist_import'),
    path('export', views.export_playlist, name='export')
]
