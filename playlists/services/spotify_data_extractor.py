import os
import spotipy
import json
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve Spotify API credentials from environment variables
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Initialize Spotify client with OAuth for user authorization
spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-modify-private playlist-read-private"))
username = 12139200429  # Placeholder for user ID, consider replacing with dynamic user input

# Attempt to get user token, remove cache and retry if failed
try:
    token = util.prompt_for_user_token(username)
except:
    os.remove(f".cache-{username}")  # Remove cached token file
    token = util.prompt_for_user_token(username)  # Retry token generation

def fetch_playlist_data(playlist_id):
    formatted_data = []  # List to hold processed tracks data
    auto_incrementing_album_id = 6900000000000000000  # Starting point for custom album ID
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
                # Compile relevant track information into a dictionary
                track_data = {
                    'track_name': track['name'],
                    'track_id': track['external_ids'].get('isrc', ''),  # Use ISRC as a universal track ID, default to empty string if not found
                    'duration_ms': track['duration_ms'],
                    'explicit': track['explicit'],
                    'spotify_track_uri': track['id'],
                    'track_number': track['track_number'],
                    'artists': [artist['id'] for artist in track['artists']],
                    'artists_names': [artist['name'] for artist in track['artists']],
                    'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,  # Album cover art URL, None if not available
                    'album_id': auto_incrementing_album_id,
                    'album_name': track['album']['name'],
                    'album_total_tracks': track['album']['total_tracks'],
                    'release_date': track['album']['release_date']
                }
                auto_incrementing_album_id += 1  # Increment custom album ID for next track
                formatted_data.append(track_data)  # Add processed track data to list

        offset += len(playlist_tracks)  # Increase offset for next batch of tracks

    return formatted_data  # Return all processed tracks data

# Replace placeholder with actual Spotify playlist ID
playlist_id = '7oCnZ5kZMdUa0hh0vjwIVt' #eventually we will grab the information from the playlist home page
playlist_data = fetch_playlist_data(playlist_id)  # Fetch all data for specified playlist

# Display the first 10 entries of the playlist data for quick inspection
first_10_entries = playlist_data[:10]
first_10_entries_str = json.dumps(first_10_entries, indent=4)
print(first_10_entries_str)

# Determine the directory two levels up from the script's location
target_dir = os.path.join(os.path.dirname(__file__), '..', '..')

os.makedirs(target_dir, exist_ok=True)  # Create target directory if it doesn't exist

# Save the fetched playlist data to a JSON file in the target directory
with open(os.path.join(target_dir, 'sample_playlist.json'), 'w') as f:
    json.dump(playlist_data, f, indent=4)  # Write data with pretty-print formatting
