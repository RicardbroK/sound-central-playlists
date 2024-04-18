# Authored By Harry McLane aka bigschlime
import json
import os
import pprint
import requests
from dotenv import load_dotenv
from datetime import datetime
from playlists.models import Artist, Track, Playlist, PlaylistTrack
import math
from django.contrib.auth.models import User

# Load environment variables containing Spotify API credentials
load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")


class spotify_playlist_info(object):
    def __init__(self, url, user):
        self.url = url
        self.creating_user = user

    def get_token(self):
        """Fetches an OAuth token from Spotify."""
        endpoint = 'https://accounts.spotify.com/api/token'
        data = f"grant_type=client_credentials&client_id={SPOTIPY_CLIENT_ID}&client_secret={SPOTIPY_CLIENT_SECRET}"
        response = requests.post(endpoint, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
        return response.json()['access_token']

    def get_paging(self, playlist_url, token):
        """Recursively fetches full track details from a paginated playlist endpoint."""
        response = requests.get(playlist_url, headers={"Authorization": f'Bearer {token}'})
        playlist_details = response.json()
        track_ids = []

        # Function to extract track data
        def extract_track_data(track):
            track_data = {
                'track_name': track['name'],
                'track_id': track['external_ids'].get('isrc', ''),
                'duration_ms': track['duration_ms'],
                'explicit': track['explicit'],
                'spotify_track_uri': track['id'],
                'spotify_album_uri': track['album']['id'],
                'track_number': track['track_number'],
                'artists': {
                    f"artist{i + 1}": {
                        "artist_name": artist['name'],
                        "artist_spotify_uri": artist['id']
                    } for i, artist in enumerate(track['artists'])
                },
                'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'album_name': track['album']['name'],
                'album_total_tracks': track['album']['total_tracks'],
                'release_date': track['album']['release_date']
            }
            return track_data

        # Extract track data for each track in the playlist
        tracks = playlist_details['tracks']['items'] if 'tracks' in playlist_details else playlist_details['items']
        for item in tracks:
            track = item['track']
            if track:  # Ensure the track details are present
                track_ids.append(extract_track_data(track))

        # Handle pagination if there are more tracks to fetch
        next_page = playlist_details['tracks']['next'] if 'tracks' in playlist_details else playlist_details['next']
        if next_page:
            track_ids.extend(self.get_paging(next_page, token))

        return track_ids

    def fetch_playlist_info(self):
        """Fetches detailed information about a Spotify playlist and writes it to a file."""
        playlist_id = self.url.split("playlist/")[1].split("?")[0]  # Extract playlist ID from URL
        endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}'
        token = self.get_token()

        response = requests.get(endpoint, headers={"Authorization": f'Bearer {token}'})
        playlist_details = response.json()

        playlist_data = {
            'spotify_playlist_id': playlist_details['id'],
            'creator_name': playlist_details['owner']['display_name'],
            'playlist_name': playlist_details['name'],
            'playlist_description': playlist_details['description'],
            'playlist_image': playlist_details['images'][0]['url'] if playlist_details['images'] else None,
            'total_tracks': playlist_details['tracks']['total'],
            'playlist_tracks': self.get_paging(endpoint, token)
        }

        # # Check for existing playlist
        # existing_playlist = Playlist.objects.filter(spotify_playlist_uri=playlist_data['spotify_playlist_id']).first()
        # if existing_playlist:
        #     print(f"Playlist with Spotify ID {playlist_data['spotify_playlist_id']} already exists.")
        #     # Optionally update existing_playlist here
        #     return existing_playlist.playlist_id

        # Continue with adding new playlist, tracks, and albums
        playlist_tracks = []
        for item in playlist_data['playlist_tracks']:
            try:
                release_date = datetime.strptime(item['release_date'], "%Y-%m-%d")
            except ValueError:
                year = item['release_date'].split("-")[0]
                release_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")

            artists = []
            for artist_key, artist_value in item['artists'].items():
                artist, _ = Artist.objects.get_or_create(
                    artist_name=artist_value['artist_name'],
                    defaults={'spotify_artist_uri': artist_value['artist_spotify_uri']}
                )
                if artist.spotify_artist_uri is None or artist.spotify_artist_uri == '':
                    print(artist)
                    artist.spotify_artist_uri = artist_value['artist_spotify_uri']
                    artist.save()
                artists.append(artist)

            track, _ = Track.objects.get_or_create(
                track_id=item['track_id'],
                defaults={
                    'track_name': item['track_name'],
                    'duration_ms': item['duration_ms'],
                    'duration_ms_rounded': math.ceil(item['duration_ms'] / 1000) * 1000,
                    'explicit': item['explicit'],
                    'track_number': item['track_number'],
                    'spotify_track_uri': item['spotify_track_uri'],
                    'album_art_url': item['album_art'],
                    'album_title': item['album_name'],
                    'release_date': release_date,
                    'original_platform': 'spotify',
                    'offical_track': True
                }
            )

            for artist in artists:
                track.artists.add(artist)

            playlist_tracks.append(track)

        playlist, _ = Playlist.objects.get_or_create(
            spotify_playlist_uri=playlist_data['spotify_playlist_id'],
            playlist_track_length=len(playlist_tracks),
            playlist_image=playlist_data['playlist_image'],
            playlist_description=playlist_data['playlist_description'],
            user=self.creating_user,
            defaults={
                'playlist_name': playlist_data['playlist_name'],
                'user': self.creating_user,
                'playlist_description': playlist_data['playlist_description'],
                'playlist_track_length': len(playlist_tracks),  # Updated from 'total_tracks'
                'playlist_image': playlist_data['playlist_image']
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
