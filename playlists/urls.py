from django.urls import path
from .views import home
from . import views

urlpatterns = [
    path('create/', home.as_view(), name='create'),
    path('view', views.view_playlist),
    path('topPlaylists/', views.topPlaylists , name='topPlaylists'),
    path('myPlaylists/', views.myPlaylists , name='myPlaylists'),
    path('import/', views.importPage , name='import'),
    path('', views.homepage , name='home'),
    path('saved/', views.saved_playlists)
]
