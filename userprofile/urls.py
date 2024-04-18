from django.urls import path
from . import views

urlpatterns = [
    path('', views.viewprofile),
    path('get-spotify', views.spotify_oauth, name='get-spotify'),
    path('spotify', views.spotify_callback)
]
