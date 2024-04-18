from django.urls import include, path
from django.contrib import admin
from .views import importPlaylist, exportPlaylist
from . import views

urlpatterns = [
    path('import/', importPlaylist.as_view(), name='import'),
    path('view/<int:playlist_id>', views.view_playlist, name='view'),
    path('view/save', views.save_playlist),
    path('', views.user_playlists, name='myPlaylists'),
    path('topPlaylists/', views.topPlaylists , name='topPlaylists'),
    path('signup/', views.signup, name='signup'),
    path('saved/', views.saved_playlists),
    path('export', exportPlaylist.as_view(), name='export'),
    path('logout/', views.logout)
]
