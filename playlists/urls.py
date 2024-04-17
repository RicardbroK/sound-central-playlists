from django.urls import include, path
from django.contrib import admin
from .views import home
from . import views

urlpatterns = [
    path('create/', home.as_view(), name='create'),
    path('view', views.view_playlist),
    path('topPlaylists/', views.topPlaylists , name='topPlaylists'),
    path('myPlaylists/', views.myPlaylists , name='myPlaylists'),
    path('import/', views.importPage , name='import'),
    path('signup/', views.signup, name='signup'),
    path('', views.homepage , name='home'),
    path('saved/', views.saved_playlists),
    path('logout/', views.logout)
]