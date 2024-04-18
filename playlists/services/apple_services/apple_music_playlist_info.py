import os
import datetime
import jwt
import cryptography
import requests

# set up the authentication for Apple Music using dev token


# requires pyjwt (https://pyjwt.readthedocs.io/en/latest/)
# pip install pyjwt


APPLE_MUSIC_API_KEY = os.getenv('APPLE_MUSIC_API_KEY')
APPLE_MUSIC_TEAM_ID = os.getenv('APPLE_MUSIC_TEAM_ID')
APPLE_MUSIC_DEV_KEY = os.getenv('APPLE_MUSIC_DEV_KEY')
alg = 'ES256'


def get_apple_music_token():
    time_now = datetime.datetime.now()
    time_expired = datetime.datetime.now() + datetime.timedelta(hours=12)

    headers = {
        "alg": alg,
        "kid": APPLE_MUSIC_DEV_KEY
    }

    payload = {
        "iss": APPLE_MUSIC_TEAM_ID,
        "exp": int(time_expired.timestamp()),  # Changed to use .timestamp() method
        "iat": int(time_now.timestamp())  # Changed to use .timestamp() method
    }
    token = jwt.encode(payload, APPLE_MUSIC_API_KEY, algorithm=alg, headers=headers)

    return token


def apple_music_playlist_info(playlist_info, playlist_songs):

    track_ids = []

    def extract_track_data(track):
        track_data = {
            'track_name': track['attributes']['name'],
            'duration_ms': track['attributes']['duration_ms'],
            'explicit': track['attributes']['contentRating'],
            'apple_track_uri': track['id'],
            'track_number': track['track_number'],
            'artists': {
                f"artist{i + 1}": {
                    "artist_name": track['attributes']['artistName'],
                } for i, artist in enumerate(track['artists'])
            },
            'album_art': track['attributes']['artwork']['url'] if track['attributes']['artwork']['url'] else None,
            'album_name': track['attributes']['albumName'],
            'release_date': track['attributes']['release_date']
        }

        return track_data

    #grab playlist data from the request
    playlist_details = playlist_info[0]
    playlist_data = {
        'apple_playlist_id': playlist_details['id'],
        'playlist_name': playlist_details['attributes']['name'],
        'playlist_description': playlist_details['attributes']['description']['standard'] if
        playlist_details['attributes']['description']['standard'] else None,
        'playlist_image': playlist_details['attributes']['artwork']['url'] if playlist_details['attributes'][
            'artwork'] else None,
    }