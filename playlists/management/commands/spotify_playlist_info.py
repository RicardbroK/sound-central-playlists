import spotipy
import json
import os
import pprint
from dotenv import load_dotenv
from spotipy import SpotifyOAuth

load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-modify-private playlist-read-private"))
username = '12139200429'  # Update this with the actual user ID or retrieve dynamically

def get_paging(playlist_url):
    playlist_url = input("Enter playlist url: ")
    playlist_id = playlist_url.split("playlist/")[1].split("?si=")[0]
    playlist_track_ids = []
    if playlist_details['tracks']['next']:
        for item in playlist_details['tracks']['items']:
            playlist_track_ids.append(item['track']['external_ids'].get('isrc', ''))
        playlist_track_ids.extend(get_paging(playlist_details['tracks']['next']))
    return playlist_track_ids


def fetch_playlist_info():
    playlist_url = input("Enter playlist url: ")
    playlist_id = playlist_url.split("playlist/")[1].split("?si=")[0]
    playlist_details = spotify.playlist(playlist_id)
    formatted_data = []  # List to hold processed tracks data
    # Loop to handle pagination and fetch all tracks
    playlist_data = {
        'original_playlist_id': playlist_details['id'],
        'creator_name': playlist_details['owner']['display_name'],
        'original_service_user_id': playlist_details['owner']['display_name'],
        'playlist_name': playlist_details['name'],
        'playlist_image': playlist_details['images'][0]['url'],
        'playlist_tracks' : get_paging(playlist_url)
    }

    formatted_data.append(playlist_data)

    return formatted_data  # Return all processed tracks data


with open('playlist_details2.json', 'w') as f:
    json.dump(fetch_playlist_info(), f, indent=4)
