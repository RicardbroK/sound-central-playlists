import os
import spotipy
import json
import spotipy.util as util
import pprint
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()
# call the varibles set in the .env file
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI =  os.getenv("SPOTIPY_REDIRECT_URI")
#using Spotify's OAuth to prompt the user to authorize the app.
# Set the scope to what is needed to create the playlist
# private playlist creation needs this scope: scope = "playlist-modify-private playlist-read-private"
# public playlist creation requires this scope: scope = "playlist-modify-public playlist-read-public"
spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-modify-private playlist-read-private"))
username = 12139200429 #make user input at some point

# erase cache and prompt for user permission
try:
    token = util.prompt_for_user_token(username)
except:
    os.remove(f".cache-{username}")
    token = util.prompt_for_user_token(username)

def fetch_playlist_data(playlist_id):
    results = spotify.playlist(playlist_id)
    playlist_tracks = results['tracks']['items']
    formatted_data = []

    for item in playlist_tracks:
        track = item['track']
        track_data = {
            'track_name': track['name'],
            'track_id': track['id'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'track_number': track['track_number'],
            # 'album': track['album'],
            'artists':  [artist['id'] for artist in track['artists']],
            'artists_names':[artist['name'] for artist in track['artists']],
            'album_id' : track['album']['id'],
            'album_name' : track['album']['name'],
            'album_total_tracks' : track['album']['total_tracks'],
            'release_date' : track['album']['release_date']
        }
        formatted_data.append(track_data)

    return formatted_data


# Replace 'playlist_id' with the actual Spotify playlist ID
playlist_id = '7oCnZ5kZMdUa0hh0vjwIVt' # extract this from the playlists homepage user input
playlist_data = fetch_playlist_data(playlist_id)

# Display the first 10 entries of the playlist data
first_10_entries = playlist_data[:10]
first_10_entries_str = json.dumps(first_10_entries, indent=4)
print(first_10_entries_str)

# Define the target directory two levels up from the current script location
target_dir = os.path.join(os.path.dirname(__file__), '..', '..')

# Ensure the target directory exists
os.makedirs(target_dir, exist_ok=True)

# Save the playlist data to 'sample_playlist.json' in the target directory
with open(os.path.join(target_dir, 'sample_playlist.json'), 'w') as f:
    json.dump(playlist_data, f, indent=4)