from .views import apple_music_playlist_info, importPlaylist, exportPlaylist
from django.urls import include, path
from django.contrib import admin
from . import views

urlpatterns = [
    path('import/', importPlaylist.as_view(), name='import'),
    path('import/apple/<str:apple_playlist_id>', views.apple_import_view, name='import_apple_confirm'),
    path('view/<int:playlist_id>', views.view_playlist, name='view'),
    path('view/save', views.save_playlist),
    path('', views.user_playlists, name='myPlaylists'),
    path('topPlaylists/', views.topPlaylists , name='topPlaylists'),
    path('signup/', views.signup, name='signup'),
    path('saved/', views.saved_playlists, name = 'saved_playlists'),
    path('apple/', views.apple_music_playlist_info, name='apple_playlist_import'),
    path('export', exportPlaylist.as_view(), name='export'),
    path('logout/', views.logout),
    path('apple/generateToken/', views.apple_generate_token.as_view(), name='apple_generate_token'),
]
