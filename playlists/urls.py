from django.urls import path
from .views import home
from . import views

urlpatterns = [
    path('create/', home.as_view(), name='create'),
    path('view', views.view_playlist),
    path('', views.user_playlists),
    path('saved/', views.saved_playlists)
]
