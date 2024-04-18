import os
import pprint
import json
from datetime import datetime, timedelta
import jwt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
from playlists.models import Playlist, Track, Artist
from .serializers import PlaylistSerializer
from playlists.services.spotify_services.spotify_playlist_info import spotify_playlist_info
from playlists.services.youtube_services.yt_music_playlist_info import youtube_playlist_info
from playlists.services.apple_services.apple_music_playlist_info import apple_music_playlist_info


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
            match parsed_url.hostname:
                case 'music.apple.com':
                    # Apple Music token generation logic
                    time_now = datetime.now()
                    time_expired = time_now + timedelta(hours=12)
                    headers = {
                        "alg": 'ES256',
                        "kid": str(os.getenv("APPLE_MUSIC_DEV_KEY"))
                    }
                    payload = {
                        "iss": os.getenv("APPLE_MUSIC_TEAM_ID"),
                        "exp": int(time_expired.timestamp()),
                        "iat": int(time_now.timestamp())
                    }
                    token = jwt.encode(payload, os.getenv("APPLE_MUSIC_API_KEY"), algorithm='ES256', headers=headers)
                    context['token'] = token
                    # You might want to use this token for subsequent requests to the Apple Music API
                    print(token)  # For debugging

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
                    case 'apple_music':
                        context['test_variable'] = 'you made it to apple'
                    case _:
                        raise ValueError("Unsupported platform or an error occurred in matching the platform.")
                playlist_details = Playlist.objects.get(playlist_id=playlist_id)
                serializer = PlaylistSerializer(playlist_details, many=False)
                formatted_data = serializer.data
            except Exception as e:
                print(f"An error occurred: {e}")
                # context['valid_url'] = False
                return render(request, 'playlists/home.html', context=context)
            context['formatted_data'] = formatted_data
            return render(request, 'playlists/view.html', context=context)
        else:
            return render(request, 'playlists/home.html', context=context)


def view_playlist(request):
    return HttpResponse('Viewing playlist here')


def user_playlists(request):
    return HttpResponse('Viewing my playlists here')


def saved_playlists(request):
    return HttpResponse('Viewing saved playlist here')


def import_playlist(output_data):
    # Check for existing playlist
    existing_playlist = Playlist.objects.filter(
        spotify_playlist_uri=output_data['playlist_information']['apple_playlist_uri']).first()
    if existing_playlist:
        print(
            f"redirect to the spotify playlist {output_data['playlist_information']['spotify_playlist_id']} as it already exists.")
        # Optionally update existing_playlist here
        return existing_playlist.playlist_id

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
                'original_platform': 'apple'
            }
        )

        playlist_tracks.append(track)

    playlist, _ = Playlist.objects.get_or_create(
        apple_playlist_uri=output_data['playlist_information']['apple_playlist_uri'],
        defaults={
            'playlist_name': output_data['playlist_information']['playlist_name'],
            'playlist_description': output_data['playlist_information']['playlist_description'],
            'playlist_track_length': len(playlist_tracks),  # Updated from 'total_tracks'
            'playlist_image': output_data['playlist_information']['playlist_image'],
            'apple_playlist_uri': output_data['playlist_information']['apple_playlist_uri']
        }
    )

    for track in playlist_tracks:
        playlist.tracks.add(track)

    print(f"Successfully added/updated playlist: {playlist.playlist_name}")
    return playlist.playlist_id


@csrf_exempt
@require_http_methods(["POST"])
def apple_music_playlist_info(request):
    try:
        data = json.loads(request.body)
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
            import_playlist(output_data)
            return JsonResponse({'message': 'Input playlist successfully'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Error processing JSON data'}, status=400)
