from .views import home, apple_music_playlist_infofrom, importPlaylist, exportPlaylist
from django.urls import include, path
from django.contrib import admin
from . import views

urlpatterns = [
    path('import/', importPlaylist.as_view(), name='import'),
    path('view/<int:playlist_id>', views.view_playlist, name='view'),
    path('view/save', views.save_playlist),
    path('', views.user_playlists, name='myPlaylists'),
    path('topPlaylists/', views.topPlaylists , name='topPlaylists'),
    path('signup/', views.signup, name='signup'),
    path('saved/', views.saved_playlists),
    path('apple/', views.apple_music_playlist_info, name='apple_playlist_import'),
    path('export', exportPlaylist.as_view(), name='export'),
    path('logout/', views.logout)
]
