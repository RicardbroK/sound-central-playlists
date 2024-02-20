# Authored By Harry McLane aka bigschlime
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables containing Spotify API credentials
load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

def get_token():
    """Fetches an OAuth token from Spotify."""
    endpoint = 'https://accounts.spotify.com/api/token'
    data = f"grant_type=client_credentials&client_id={SPOTIPY_CLIENT_ID}&client_secret={SPOTIPY_CLIENT_SECRET}"
    response = requests.post(endpoint, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()['access_token']

def get_paging(playlist_url, token):
    """Recursively fetches full track details from a paginated playlist endpoint."""
    response = requests.get(playlist_url, headers={"Authorization": f'Bearer {token}'})
    playlist_details = response.json()
    track_ids = []

    # Function to extract track data
    def extract_track_data(track):
        track_data = {'track_name': track['name'], 'track_id': track['external_ids'].get('isrc', ''), 'duration_ms': track['duration_ms'], 'explicit': track['explicit'], 'spotify_track_uri': track['id'], 'spotify_album_uri': track['album']['id'], 'track_number': track['track_number'], 'artists': {f"artist{i + 1}": {"artist_name": artist['name'], "artist_spotify_uri": artist['id']} for i, artist in enumerate(track['artists'])}, 'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None, 'album_name': track['album']['name'], 'album_total_tracks': track['album']['total_tracks'], 'release_date': track['album']['release_date']}
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
        track_ids.extend(get_paging(next_page, token))

    return track_ids

def fetch_playlist_info():
    """Fetches detailed information about a Spotify playlist and writes it to a file."""
    playlist_url = input("Enter playlist URL: ")
    playlist_id = playlist_url.split("playlist/")[1].split("?")[0]  # Extract playlist ID from URL
    endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    token = get_token()

    response = requests.get(endpoint, headers={"Authorization": f'Bearer {token}'})
    playlist_details = response.json()

    playlist_data = {'spotify_playlist_id': playlist_details['id'], 'creator_name': playlist_details['owner']['display_name'], 'playlist_name': playlist_details['name'], 'playlist_description': playlist_details['description'], 'playlist_image': playlist_details['images'][0]['url'] if playlist_details['images'] else None, 'total_tracks': playlist_details['tracks']['total'], 'playlist_tracks': get_paging(endpoint, token)}

    # Write fetched playlist data to a JSON file
    with open('../../../playlist_details.json', 'w') as f:
        json.dump([playlist_data], f, indent=4)

fetch_playlist_info()
