import os
from googleapiclient.discovery import build

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

class youtube_playlist_info(object):
    def __init__(self, id):
        self.id = id
        print(self.id)

    def get_paging(self, playlist_url, token):
       return None

    def get_playlist_info(self):
        response = youtube.playlists().list(
            part="snippet,contentDetails",
            id=f'{self.id}'
        ).execute()
        playlist_details = response["items"][0]
        playlist_data = {'yt_music_playlist_id': playlist_details['id'],
                         'creator_name': playlist_details['snippet']['channelTitle'],
                         'playlist_name': playlist_details['snippet']['title'],
                         'playlist_description': playlist_details['snippet']['description'],
                         'playlist_image': playlist_details['snippet']['thumbnails']['default']['url'],
                         'total_tracks': playlist_details['contentDetails']['itemCount'],
                         }
                         #'playlist_tracks': self.get_paging(endpoint, token)}
        #add data to the DB
        print(playlist_data)
        return playlist_data