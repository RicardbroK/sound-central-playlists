from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt

# Create your views here.

def home(request):
   return render(request, 'home.html')

def view_playlist(request):
   return HttpResponse('Viewing playlist here')

def user_playlists(request):
    return HttpResponse('Viewing my playlists here')

def saved_playlists(request):
   return HttpResponse('Viewing saved playlist here')