from django.core.management.base import BaseCommand
import os
import spotipy
import json
from spotipy.oauth2 import SpotifyOAuth



class Command(BaseCommand):
    help = 'Fetches data from a Spotify playlist and saves it to a JSON file'

    def handle(self, *args, **options):
        spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-modify-private playlist-read-private"))
        username = '12139200429'  # Update this with the actual user ID or retrieve dynamically

        # Function to extract playlist ID from a Spotify playlist link
        def extract_playlist_id(playlist_link):
            return playlist_link.split("playlist/")[1].split("?si=")[0]

        # Function to fetch playlist data
        def fetch_playlist_data(playlist_id):
            formatted_data = []  # List to hold processed tracks data
            auto_incrementing_album_id = 690000000  # Starting point for custom album ID
            offset = 0  # Offset for pagination

            # Loop to handle pagination and fetch all tracks
            while True:
                results = spotify.playlist_tracks(playlist_id, offset=offset)  # Fetch tracks with current offset
                playlist_tracks = results['items']  # Extract tracks from results

                if not playlist_tracks:  # Exit loop if no more tracks are returned
                    break

                # Process each track in the current batch
                for item in playlist_tracks:
                    track = item['track']
                    if track:  # Ensure track data is not None
                        artists_dict = {}
                        for i, artist in enumerate(track['artists']):
                            artist_key = f"artist{i + 1}"
                            artists_dict[artist_key] = {
                                "artist_name": artist['name'],
                                "artist_spotify_uri": artist['id']
                            }

                        track_data = {
                            'spotify_playlist_id': playlist_id,
                            'track_name': track['name'],
                            'track_id': track['external_ids'].get('isrc', ''),
                            'duration_ms': track['duration_ms'],
                            'explicit': track['explicit'],
                            'spotify_track_uri': track['id'],
                            'spotify_album_uri': track['album']['id'],
                            'track_number': track['track_number'],
                            'artists': artists_dict,
                            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                            'album_id': auto_incrementing_album_id,
                            'album_name': track['album']['name'],
                            'album_total_tracks': track['album']['total_tracks'],
                            'release_date': track['album']['release_date']
                        }
                        auto_incrementing_album_id += 1
                        formatted_data.append(track_data)

                offset += len(playlist_tracks)

            return formatted_data

        # Prompt for playlist link and fetch data
        playlist_link = input('Paste in your playlist link: ')
        playlist_id = extract_playlist_id(playlist_link)
        playlist_data = fetch_playlist_data(playlist_id)

        # Save fetched data to a JSON file
        with open('sample_playlist.json', 'w') as f:
            json.dump(playlist_data, f, indent=4)

        self.stdout.write(self.style.SUCCESS('Successfully fetched playlist data'))
