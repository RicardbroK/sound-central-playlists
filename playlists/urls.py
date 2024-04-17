from django.urls import include, path
from django.contrib import admin
from .views import home
from . import views

urlpatterns = [
    path('create/', home.as_view(), name='create'),
    path('view/<int:playlist_id>', views.view_playlist, name='view'),
    path('view/save', views.save_playlist),
    path('', views.user_playlists),
    path('signup/', views.signup, name='signup'),
    path('saved/', views.saved_playlists),
    path('export', views.export_playlist, name='export'),
    path('logout/', views.logout)
]