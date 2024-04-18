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
from django.contrib.auth.models import User
import requests
import urllib.parse

# Create your views here.
class importPlaylist(APIView):
    def get(self, request):
        return render(request, 'playlists/import.html')

    def post(self, request):
        playlist_url = request.POST.get('playlisturl')
        context = {'developer_token': ''}
        playlist_id = 0

        # #don't allow guests to make playlists
        # if not request.user.is_authenticated:
        #     return render(request, 'playlists/home.html', context=context)

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
                    return url.split("?list=")[1].split("&si=")[0]
                case _:
                    return 'unknown'

        context['valid_url'] = url_is_valid = valid_url(playlist_url)
        context['platform'] = url_platform = get_platform_name(playlist_url)
        if url_is_valid and url_platform != 'unsupported': #and request.user.is_authenticated:
            context['playlist_id'] = playlist_id = get_playlist_id(playlist_url)
            # make sure that url is fully working
            try:
                match url_platform:
                    case 'spotify':
                        sur = spotify_playlist_info(playlist_url, request.user)
                        playlist_id = sur.fetch_playlist_info()
                    case 'yt_music':
                        yur = youtube_playlist_info(playlist_id, request.user)
                        playlist_id = yur.insert_playlist_db()
                    case _:
                        raise ValueError("Unsupported platform or an error occurred in matching the platform.")
            except Exception as e:
                print(f"An error occurred: {e}")
                context['valid_url'] = False
                return render(request, 'playlists/import.html', context=context)
            return redirect(view_playlist, playlist_id=playlist_id)#f'/playlists/view?playlist_id={playlist_id}')
        else:
            return render(request, 'playlists/import.html', context=context)

def view_playlist(request, playlist_id):
    context = {}
    try:
        playlist_details = Playlist.objects.get(playlist_id=playlist_id)
        serializer = PlaylistSerializer(playlist_details, many=False)
        playlist_details = serializer.data
        if request.user.id in playlist_details['fans']:
            context['playlist_saved'] = True
        else:
            context['playlist_saved'] = False
        #remove fans from playlistf details so it is not visbile in javascript.
        playlist_details.pop('fans')
        context['playlist_data'] = playlist_details
        context['playlist_creator_name'] = User.objects.get(id=playlist_details['user']).username
        return render(request, 'playlists/view.html', context=context)
    except Exception as e:
        return HttpResponse(f'{e}')

@login_required(redirect_field_name="my_redirect_field")
def user_playlists(request):
    context= {}
    current_user = request.user
    if current_user.is_authenticated:
        #Get all playlists created by current user
        user_playlists = Playlist.objects.filter(user=current_user)
        context['playlists'] = user_playlists
        return render(request, 'playlists/userPlaylists.html', context=context)
    else:
        return HttpResponse(f'User is not authenticated')
    
@login_required(redirect_field_name="my_redirect_field")
def saved_playlists(request):
    context= {}
    current_user = request.user
    if current_user.is_authenticated:
        #Get all playlists current user is a fan of
        saved_playlists = Playlist.objects.filter(fans__id=current_user.id)
        context['saved_playlists'] = saved_playlists
        return render(request, 'playlists/savedPlaylists.html', context=context)
    else:
        return HttpResponse(f'User is not authenticated')

class exportPlaylist(APIView):
    def get(self, request):
        context = {}
        context['platform']= request.GET.get('platform')
        context['playlist_id'] = request.GET.get('id')

        playlist_details = PlaylistSerializer(Playlist.objects.get(playlist_id=context['playlist_id'])).data
        playlist_details.pop('fans')
        context['playlist_details'] = playlist_details
        context['confirm_needed'] = True
        confirmed = request.POST.get('confirm') == 'Confirmed'

        return render(request, 'playlists/export.html', context=context)
    
    def post(self, request):
        TRACK_SEARCH_LIMIT = 1
        SPOTIFY_URL_START = 'https://api.spotify.com/v1/search?q='
        SPOTIFY_URL_END = f'&type=track&limit={TRACK_SEARCH_LIMIT}'
        def search_spotify_uri(track) -> str:
            spotify_token = json.loads(request.session.get('spotify'))['access_token']
            if track['spotify_track_uri'] == '' or track['spotify_track_uri'] is None:
                track_name = track['track_name']
                if track['offical_track'] and track['original_platform'] != 'yt_music':
                    isrc = track['track_id']
                    endpoint = f'{SPOTIFY_URL_START}isrc%3A{isrc}{SPOTIFY_URL_END}'
                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                    response = requests.get(endpoint, headers=header)
                    print(response.content)
                    try:
                        return response.json()['tracks']['items'][0]['uri']
                    except:
                        print('Offical track, ISRC not found, finding alternative.')
                        artist = track['artists'][0]['artist_name']
                        track_name = track['track_name']
                        track_album_title = track['album_title']
                        searchterms=  urllib.parse.quote(f'{track_name} {artist} artist:{artist} album:{track_album_title}').replace('%20', '+')
                        endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                        header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                        response = requests.get(endpoint, headers=header)
                        print(response.status_code)
                        if response.status_code == 200:
                            try:
                                return response.json()['tracks']['items'][0]['uri']
                            except Exception as e:
                                print(response.content)
                                print('First search failed.')
                                try:
                                    searchterms= urllib.parse.quote(f'q={track_name} {artist} artist:{artist}').replace('%20', '+')
                                    endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                                    response = requests.get(endpoint, headers=header)
                                    return response.json()['tracks']['items'][0]['uri']
                                except:
                                    print(response.content)
                                    print('Final search failed, skipping.')
                                    return False
                        else:
                            print(response.content)
                            print(track_name)
                            print(endpoint)
                            print('Track skipped.')
                            return False   
                elif track['offical_track']:
                    artist = track['artists'][0]['artist_name']
                    track_album_title = track['album_title']
                    searchterms= urllib.parse.quote(f'{track_name} {artist} artist:{artist} album:{track_album_title}').replace('%20', '+')
                    endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                    response = requests.get(endpoint, headers=header)
                    print(response.status_code)
                    if response.status_code == 200:
                        try:
                            return response.json()['tracks']['items'][0]['uri']
                        except Exception as e:
                            print(response.content)
                            print('First search failed.')
                            try:
                                searchterms= urllib.parse.quote(f'{track_name} {artist} artist:{artist}').replace('%20', '+')
                                endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                                header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                                response = requests.get(endpoint, headers=header)
                                return response.json()['tracks']['items'][0]['uri']
                            except:
                                print(response.content)
                                print('Final search failed, skipping.')
                                return False
                    else:
                        print(response.content)
                        print(track_name)
                        print(endpoint)
                        print('Track skipped.')
                        return False
                else:
                    searchterms= urllib.parse.quote(f'{track_name}').replace('%20', '+')
                    endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                    response = requests.get(endpoint, headers=header)
                    print(response.status_code)
                    if response.status_code == 200:
                        try:
                            return response.json()['tracks']['items'][0]['uri']
                        except Exception as e:
                            print('Unofficial track, no track found, skipping.')
                            return False
                    else:
                        print(response.content)
                        print(track_name)
                        print(endpoint)
                        print('Track skipped.')
                        return False
            else:
                return 'spotify:track:'+track['spotify_track_uri']
        
        context = {}
        context['platform']= request.GET.get('platform')
        context['playlist_id'] = request.GET.get('id')

        playlist_details = PlaylistSerializer(Playlist.objects.get(playlist_id=context['playlist_id'])).data
        playlist_details.pop('fans')
        context['playlist_details'] = playlist_details
        confirmed = request.POST.get('confirm') == 'Confirmed'

        match context['platform']:
            case 'spotify':
                spotify_session = request.session.get('spotify')
                if spotify_session is not None:
                    if confirmed:
                        spotify_token = json.loads(spotify_session)['access_token']
                        endpoint = 'https://api.spotify.com/v1/me'
                        header= {'Authorization': 'Bearer'+f' {spotify_token}'}
                        response = requests.get(endpoint, headers=header)
                        print(response)
                        if response.status_code == 200: 
                            spotify_user_data = response.json()
                            spotify_user_uri = spotify_user_data['uri'].split(':')[2]
                            endpoint = f'https://api.spotify.com/v1/users/{spotify_user_uri}/playlists'
                            header.update({'Content-Type': 'application/json'})
                            data = json.dumps({ 
                                    'name': f"{playlist_details['playlist_name']}",
                                    "description": f"{playlist_details['playlist_description']}",
                                    "public": 'false' 
                            })
                            response = requests.post(endpoint, headers=header, data=data)
                            spotify_playlist_uri = response.json()['uri'].split(':')[2]
                            if response.status_code == 201:
                                endpoint = f'https://api.spotify.com/v1/playlists/{spotify_playlist_uri}/tracks'
                                full_track_uri_list = []
                                for playlist_track in playlist_details['tracks']:
                                    track = playlist_track['track']
                                    uri = search_spotify_uri(track)
                                    if uri:
                                        full_track_uri_list.append(f'{uri}')
                                track_uri_list_chunks = [full_track_uri_list[i:i + 100] for i in range(0, len(full_track_uri_list), 100)]
                                print(track_uri_list_chunks)
                                for track_uri_list_chunk in track_uri_list_chunks:
                                    data = json.dumps({
                                            'uris': track_uri_list_chunk,
                                            'position': 0
                                    })
                                    response = requests.post(endpoint, headers=header, data=data)
                                context['success'] = True
                                context['spotify_playlist_uri'] = spotify_playlist_uri
                                context['confirm_needed'] = True
                    else:
                        context['confirm_needed'] = True
                else:
                    context['spotify_access_expired'] = True
            case _:
                breakpoint
        return render(request, 'playlists/export.html', context=context)

def save_playlist(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    playlist_to_save = body['id']
    current_user = request.user
    if request.user.is_authenticated and playlist_to_save is not None:
        playlist = Playlist.objects.get(playlist_id=playlist_to_save)
        if not (playlist.user == current_user):
            if current_user in playlist.fans.all():
                playlist.fans.remove(current_user)
                return HttpResponse(f'{current_user.username} has removed themselves from playlist {playlist_to_save}')
            else:
                playlist.fans.add(current_user)
                return HttpResponse(f'{current_user.username} has saved playlist {playlist_to_save}')
        return HttpResponse(f'Failed to save')
    else:
        return HttpResponse(f'Failed to save')
def homepage(request):
    return render(request, "playlists/home.html")

def topPlaylists(request):
    return render(request, "playlists/topPlaylists.html")
def signup(request):
    return render(request, "registration/signup.html")
def logout_view(request):
    logout(request)
    return redirect("/")