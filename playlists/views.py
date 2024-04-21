import os
from django.urls import reverse
import pprint
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
from playlists.models import Playlist, Track, Artist, PlaylistTrack
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm  
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from playlists.models import Playlist
from .serializers import PlaylistSerializer
from playlists.services.spotify_services import spotfiy_extra_services, spotify_playlist_info
from playlists.services.youtube_services.yt_music_playlist_info import youtube_playlist_info
from playlists.services.apple_services.apple_music_playlist_info import apple_music_playlist_info
from django.conf import settings
import json
from django.shortcuts import redirect
from django.contrib.auth.models import User
import requests
from django.db.models import Count
from playlists.services.apple_services.apple_token import generate_apple_music_token

class apple_generate_token(APIView):
    def get(self, request):
        token = generate_apple_music_token()
        return JsonResponse({'apple_music_token': token}, status=200)
 
# Create your views here.
class importPlaylist(APIView):
    
    def get(self, request):
        context = {}
        context['valid_url'] = not request.GET.get('failed')
        return render(request, 'playlists/import.html', context=context)

    def post(self, request):
        playlist_url = request.POST.get('playlisturl')
        context = {}
        playlist_id = 0
        #don't allow guests to make playlists, prompt them to login
        if not request.user.is_authenticated:
            return redirect('/signup/login')

        def get_platform_name(url) -> str:
            parsed_url = urlparse(url)
            match parsed_url.hostname:
                case 'music.apple.com':
                    return 'apple_music'
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
                    # make sure it is a playlist path
                    match parsed_url.path.split('us/')[1:][0].split('/')[0:]:
                        case ['playlist', *_]:
                            return 'apple_music'
                        case _:
                            return 'unsupported'
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
                case 'apple_music':
                    return url.split('playlist/')[1].split('/')[1]
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
                        sur = spotify_playlist_info.spotify_playlist_info(playlist_url, request.user)
                        playlist_id = sur.fetch_playlist_info()
                    case 'yt_music':
                        yur = youtube_playlist_info(playlist_id, request.user)
                        playlist_id = yur.insert_playlist_db()
                    case 'apple_music':
                        request.GET._mutable = True
                        request.GET['apple'] = 'apple-import'
                        context['test_variable'] = 'you made it to apple'
                        #return render(request, 'playlists/apple.html', context=context)
                        return redirect(apple_import_view, apple_playlist_id=playlist_id)
                    case _:
                        raise ValueError("Unsupported platform or an error occurred in matching the platform.")
                playlist_details = Playlist.objects.get(playlist_id=playlist_id)
                serializer = PlaylistSerializer(playlist_details, many=False)
                formatted_data = serializer.data
            except Exception as e:
                print(f"An error occurred: {e}")
                context['valid_url'] = False
                return render(request, 'playlists/import.html', context=context)
            context['formatted_data'] = formatted_data
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
        context['valid_url'] = True
        return render(request, 'playlists/view.html', context=context)
    except Exception as e:
        return render(request, 'playlists/home.html')
    
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
    context = {}
    current_user = request.user
    if current_user.is_authenticated:
        # Get all playlists current user is a fan of
        saved_playlists = Playlist.objects.filter(fans__id=current_user.id)
        context['saved_playlists'] = saved_playlists
        return render(request, 'playlists/savedPlaylists.html', context=context)
    else:
        return HttpResponse(f'User is not authenticated')
    
def import_playlist(output_data, creating_user):
    # Check for existing playlist
    try:
        existing_playlist = Playlist.objects.get(
            apple_playlist_uri=output_data['playlist_information']['apple_playlist_uri'], user=creating_user)
        if existing_playlist:
            print(existing_playlist)
            print(
                f"redirect to the apple playlist {output_data['playlist_information']['apple_playlist_uri']} as it already exists.")
            # Optionally update existing_playlist here
            if existing_playlist.user == creating_user:
                return existing_playlist.playlist_id
    except:
        print('No existing playlist')

    # Continue with adding new playlist, tracks, and albums
    playlist_tracks = []
    for item in output_data['tracks']:
        try:
            release_date = datetime.strptime(item['release_date'], "%Y-%m-%d")
        except ValueError:
            year = item['release_date'].split("-")[0]
            release_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")

        artist, _ = Artist.objects.get_or_create(
            artist_name=item['artists'],
        )

        track, _ = Track.objects.get_or_create(
            track_id=item['track_id'],
            defaults={
                'track_name': item['track_name'],
                'duration_ms': item['duration_ms'],
                'track_number': item['track_number'],
                'apple_music_track_uri': item['apple_music_track_uri'],
                'album_art_url': item['album_art_url'],
                'album_title': item['album_title'],
                'release_date': release_date,
                'original_platform': 'apple',
                'offical_track': True
            }
        )

        playlist_tracks.append(track)

    playlist, _ = Playlist.objects.get_or_create(
        apple_playlist_uri=output_data['playlist_information']['apple_playlist_uri'],
        user = creating_user,
        defaults={
            'user': creating_user,
            'playlist_name': output_data['playlist_information']['playlist_name'],
            'playlist_description': output_data['playlist_information']['playlist_description'],
            'playlist_track_length': len(playlist_tracks),  # Updated from 'total_tracks'
            'playlist_image': output_data['playlist_information']['playlist_image'],
            'apple_playlist_uri': output_data['playlist_information']['apple_playlist_uri']
        }
    )

    for track in playlist_tracks:
        playlist_track, _ = PlaylistTrack.objects.get_or_create(
            track=track,
            playlist_position=playlist_tracks.index(track),
            defaults={
                'track': track,
                'playlist_position': playlist_tracks.index(track)
            }
        )
        playlist.tracks.add(playlist_track)
    print(f"Successfully added/updated playlist: {playlist.playlist_name}")
    return playlist.playlist_id

def apple_import_view(request, apple_playlist_id):
    context = {}
    context['apple_playlist_id'] = apple_playlist_id
    return render(request, 'playlists/apple.html', context=context)

@csrf_exempt
@require_http_methods(["POST"])
def apple_music_playlist_info(request):
    try:
        data = json.loads(request.body)
        print(data)
        playlist_info = data.get('playlist_attributes')
        playlist_songs = data.get('playlist_songs')

        if playlist_info:
            # Process playlist_info
            playlist_info_json = json.loads(playlist_info)
            pprint.pprint(playlist_info_json['attributes'])

            playlist_name = playlist_info_json['attributes']['name']
            apple_playlist_uri = playlist_info_json['attributes']['playParams']['id']
            updated_at = playlist_info_json['attributes']['lastModifiedDate']
            playlist_image = playlist_info_json['attributes']['artwork']['url']

            playlist_description = playlist_info_json['attributes'].get('description', {}).get('standard', '')

            # Extract tracks from the playlist_songs
            playlist_song_json = json.loads(playlist_songs)
            playlist_tracks = playlist_song_json

            playlist_data = {
                'playlist_name': playlist_name,
                'playlist_description': playlist_description,
                'playlist_image': playlist_image,
                'updated_at': updated_at,
                'apple_playlist_uri': apple_playlist_uri,
            }

            formatted_data = []
            for track in playlist_tracks:
                track_attributes = track['attributes']

                track_data = {
                    'track_id': track_attributes['isrc'],
                    'track_name': track_attributes['name'],
                    'duration_ms': track_attributes['durationInMillis'],
                    'track_number': track_attributes['trackNumber'],
                    'apple_music_track_uri': track['id'],
                    'album_art_url': track_attributes['artwork']['url'],
                    'album_title': track_attributes['albumName'],
                    'release_date': track_attributes['releaseDate'],
                    'original_platform': 'apple_music',
                    'artists': track_attributes['artistName']
                }
                formatted_data.append(track_data)

            # Output dictionary with structured format
            output_data = {
                'playlist_information': playlist_data,
                'tracks': formatted_data
            }
            pprint.pprint(output_data)
            current_user = request.user
            id = import_playlist(output_data, current_user)
            return JsonResponse({'message': 'Input playlist successfully', 'created_playlist': id})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Error processing JSON data'}, status=400)

class exportPlaylist(APIView):
    def get(self, request):
        """
        Handles the GET request for exporting a playlist to a specific platform.

        Args:
            request: The HTTP request object.

        Returns:
            A rendered response with context information for the export process.
        """
        context = {}
        try:
            context['platform']= request.GET.get('platform')
            context['playlist_id'] = request.GET.get('id')
            playlist_details = PlaylistSerializer(Playlist.objects.get(playlist_id=context['playlist_id'])).data
            playlist_details.pop('fans')
        except:
            # Redirect to the homepage if an exception occurs (e.g., invalid playlist ID)
            return redirect('/')
        context['playlist_details'] = playlist_details
        context['confirm_needed'] = True
        # Check the platform and handle accordingly
        match context['platform']:
            case 'spotify':
                # Check if there is an active Spotify session
                spotify_session = request.session.get('spotify')
                present_date = datetime.now()
                timestamp = int(datetime.timestamp(present_date))

                # Check if Spotify access token is still valid or exists
                print(spotify_session)
                # If none, access needs to be retrieved
                if spotify_session is None:
                    context['access_expired'] = True
                    return render(request, 'playlists/export.html', context=context)
                
                # If the access token has expired, attempt to refresh it without user needing to log in again
                # Otherwise, access needs to be retrieved
                if 'expires_at' in spotify_session:
                    if timestamp > spotify_session['expires_at']:
                        if 'refresh_token' in spotify_session:
                            try:
                                request.session['spotify'] = spotfiy_extra_services.refresh_spotify_token(spotify_session['refresh_token'])
                            except:
                                context['access_expired'] = True
                                return render(request, 'playlists/export.html', context=context)
            case _:
                # Placeholder for handling other platforms (breakpoint for debugging)
                breakpoint
        return render(request, 'playlists/export.html', context=context)
    
    def post(self, request):
        """
        Handles the POST request for exporting a playlist to a specific platform.

        Args:
            request: The HTTP request object.

        Returns:
            A rendered response with context information for the export process.
        """
        DESC_ADDON_PROMOTER = '... This playlist was generated by SoundCentral.'
        context = {}
        context['platform'] = request.GET.get('platform')
        context['playlist_id'] = request.GET.get('id')
        confirmed = request.POST.get('confirm') == 'Confirmed'
        # Check the platform and handle accordingly
        match context['platform']:
            case 'spotify':
                # Check if there is an active Spotify session
                spotify_session = request.session.get('spotify')
                if spotify_session is None:
                    context['access_expired'] = True
                    return render(request, 'playlists/export.html', context=context)
                else:
                    spotify_token = spotify_session['access_token']
            case _:
                context['confirm_needed'] = True
                return render(request, 'playlists/export.html', context=context)
        # Get playlist details
        playlist_details = PlaylistSerializer(Playlist.objects.get(playlist_id=context['playlist_id'])).data
        playlist_object = Playlist.objects.get(playlist_id=context['playlist_id'])
        playlist_details.pop('fans')
        context['playlist_details'] = playlist_details
        #Default success value
        success = None
        
        match context['platform']:
            # Export to Spotify
            case 'spotify':
                if spotify_session is not None:
                    #Check if user confirmed the export
                    if confirmed:
                        # Get user data from Spotify
                        endpoint = 'https://api.spotify.com/v1/me'
                        header= {'Authorization': 'Bearer'+f' {spotify_token}'}
                        response = requests.get(endpoint, headers=header)
                        print(response.json())
                        if response.status_code == 200: 
                            # Create a new Spotify playlist
                            spotify_user_data = response.json()
                            spotify_user_uri = spotify_user_data['uri'].split(':')[2]
                            endpoint = f'https://api.spotify.com/v1/users/{spotify_user_uri}/playlists'
                            header.update({'Content-Type': 'application/json'})
                            data = json.dumps({ 
                                    'name': f"{playlist_details['playlist_name']}",
                                    "description": f"{playlist_details['playlist_description']}"+DESC_ADDON_PROMOTER,
                                    "public": 'false' 
                            })
                            response = requests.post(endpoint, headers=header, data=data)
                            print(response)
                            spotify_playlist_uri = response.json()['uri'].split(':')[2]
                            if response.status_code == 201:
                                # Add tracks to the new playlist
                                endpoint = f'https://api.spotify.com/v1/playlists/{spotify_playlist_uri}/tracks'
                                full_track_uri_list = []
                                for playlist_track in playlist_details['tracks']:
                                    track = playlist_track['track']
                                    uri = spotfiy_extra_services.search_spotify_uri(track, spotify_token)
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
                                context['success'] = success = True
                                context['spotify_playlist_uri'] = spotify_playlist_uri
                                context['confirm_needed'] = True
                        else:
                            context['access_expired'] = True
                    else:
                        context['confirm_needed'] = True
                else:
                    context['access_expired'] = True
            case _:
                breakpoint
        # If export is a success, update number of playlist exports on playlist object.
        # Also save playlist for user.
        if success:
            if request.user.is_authenticated:
                if playlist_object.user != request.user:
                    playlist_object.fans.add(request.user)
            playlist_object.num_exports = playlist_object.num_exports+1
            playlist_object.save()

        return render(request, 'playlists/export.html', context=context)

def save_playlist(request):
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        playlist_to_save = body['id']
    except:
        return JsonResponse({'error': 'Must send JSON request.'}, status=400)
    try:
        current_user = request.user
    except:
        return JsonResponse({'error': 'Failed to save, no user'}, status=401)
    
    if playlist_to_save is None:
        return JsonResponse({'error': 'Failed to save, no playlist provided'}, status=500)
    
    if request.user.is_authenticated:
        playlist = Playlist.objects.get(playlist_id=playlist_to_save)
        if not (playlist.user == current_user):
            if current_user in playlist.fans.all():
                playlist.fans.remove(current_user)
                return JsonResponse({'user': f'{current_user.username}', 'saved': False, 'playlist_id': f'{playlist_to_save}'}, status=200)
            else:
                playlist.fans.add(current_user)
                return JsonResponse({'user': f'{current_user.username}', 'saved': True, 'playlist_id': f'{playlist_to_save}'}, status=200)
        return JsonResponse({'error': 'Failed to save, user does not have access to this playlist.'})
    else:
        return JsonResponse({'error': 'Failed to save, user not authenticated.'}, status=403)

def homepage(request):
    return render(request, "playlists/home.html")

def topPlaylists(request):
    context = {}
    # Get all playlists and sort by saves (num of fans)
    top_playlists = Playlist.objects.annotate(num_fans=Count('fans')).all().order_by('-num_fans')[:50]
    context['top_playlists'] = top_playlists
    return render(request, 'playlists/topPlaylists.html', context=context)

def signup(request):
    return render(request, "registration/signup.html")

def logout_view(request):
    logout(request)
    return redirect("/")