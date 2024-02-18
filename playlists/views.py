from rest_framework.views import APIView
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
class home(APIView):
    @csrf_exempt
    def get(self, request):
        return render(request, 'playlists/home.html')

    def post(self, request):
        print(request.POST.playlisturl)
        return HttpResponse('We made a post dammit')


def view_playlist(request):
    return HttpResponse('Viewing playlist here')


def user_playlists(request):
    return HttpResponse('Viewing my playlists here')


def saved_playlists(request):
    return HttpResponse('Viewing saved playlist here')
