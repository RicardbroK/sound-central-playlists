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


# Create your views here.
class home(APIView):
    def get(self, request):
        return render(request, 'playlists/home.html')

    def post(self, request):
        playlist_url = request.POST.get('playlisturl')
        context = {}
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
                case 'youtube.com' | 'www.youtube.com' | 'music.youtube.com':
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
            return playlist_id

        context['valid_url'] = url_is_valid = valid_url(playlist_url)
        context['platform'] = url_platform = get_platform_name(playlist_url)
        sur = spotify_playlist_info(playlist_url)
        playlist_id = sur.fetch_playlist_info()
        playlist_details = Playlist.objects.get(playlist_id=playlist_id)
        serializer = PlaylistSerializer(playlist_details, many=False)
        context['playlist_details'] = serializer.data
        if url_is_valid and url_platform != 'unsupported':
            context['playlist_id'] = get_playlist_id(playlist_url)
            return render(request, 'playlists/view.html', context=context)
        else:
            return render(request, 'playlists/home.html', context=context)


def view_playlist(request):
    return HttpResponse('Viewing playlist here')


def user_playlists(request):
    return HttpResponse('Viewing my playlists here')


def saved_playlists(request):
    return HttpResponse('Viewing saved playlist here')
