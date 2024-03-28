from rest_framework.views import APIView
from django.shortcuts import render
from django.http import HttpResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlparse
from playlists.models import Playlist
from .serializers import PlaylistSerializer
from .services.spotify_playlist_info import spotify_playlist_info
from .services.yt_music_playlist_info import youtube_playlist_info
from django.conf import settings
import json
from django.shortcuts import redirect
import requests

# Create your views here.
class home(APIView):
    def get(self, request):
        return render(request, 'playlists/home.html')

    def post(self, request):
        playlist_url = request.POST.get('playlisturl')
        context = {'developer_token': ''}
        playlist_id = 0

        def get_platform_name(url) -> str:
            parsed_url = urlparse(url)
            # check hostname to see if it is a supported platform
            match parsed_url.hostname:
                case 'www.spotify.com' | 'spotify.com' | 'open.spotify.com':
                    # make sure it is a playlist path
                    match parsed_url.path.split('/')[1:]:
                        case ['playlist', *_]:
                            return 'spotify'
                        case _:
                            return 'unsupported'
                case 'music.youtube.com':
                    # make sure it is a playlist path
                    match parsed_url.path.split('/')[1:]:
                        case ['playlist', *_]:
                            return 'yt_music'
                        case _:
                            return 'unsupported'
                case 'music.apple.com':
                    return 'apple_music'
                # all other hostname will be unsupported
                case _:
                    return 'unsupported'

        def valid_url(to_validate: str) -> bool:
            validator = URLValidator()
            try:
                validator(to_validate)
                # url is valid here
                return True
            except ValidationError as exception:
                # URL is NOT valid here.
                # handle exception..
                print(exception)
                return False

        def get_playlist_id(url) -> str:
            platform = get_platform_name(url)
            match platform:
                case 'spotify':
                    return url.split("playlist/")[1].split("?si=")[0]
                case 'yt_music':
                    return url.split("?list=")[1]
                case _:
                    return 'unknown'

        context['valid_url'] = url_is_valid = valid_url(playlist_url)
        context['platform'] = url_platform = get_platform_name(playlist_url)
        if url_is_valid and url_platform != 'unsupported':
            context['playlist_id'] = playlist_id = get_playlist_id(playlist_url)
            # make sure that url is fully working
            try:
                match url_platform:
                    case 'spotify':
                        sur = spotify_playlist_info(playlist_url)
                        playlist_id = sur.fetch_playlist_info()
                    case 'yt_music':
                        yur = youtube_playlist_info(playlist_id)
                        playlist_id = yur.insert_playlist_db()
                    case _:
                        raise ValueError("Unsupported platform or an error occurred in matching the platform.")
            except Exception as e:
                print(f"An error occurred: {e}")
                context['valid_url'] = False
                return render(request, 'playlists/home.html', context=context)
            return redirect(f'/playlists/view?playlist_id={playlist_id}')
        else:
            return render(request, 'playlists/home.html', context=context)

def view_playlist(request):
    playlist_id = request.GET.get('playlist_id')
    context = {}
    try:
        playlist_details = Playlist.objects.get(playlist_id=playlist_id)
        serializer = PlaylistSerializer(playlist_details, many=False)
        playlist_details = serializer.data
        context['playlist_data'] = playlist_details
        context['playlist_data_json'] = json.dumps(playlist_details)
        return render(request, 'playlists/view.html', context=context)
    except Exception as e:
        return HttpResponse(f'{e}')

def user_playlists(request):
    return HttpResponse('Viewing my playlists here')

def saved_playlists(request):
    return HttpResponse('Viewing saved playlist here')
