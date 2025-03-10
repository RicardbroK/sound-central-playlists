import os
from googleapiclient.discovery import build
from pprint import pprint
from playlists.models import Artist, Track, Playlist, PlaylistTrack
from datetime import datetime
import re
import isodate
import requests
import json

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_OPERATIONAL_API_URL = os.getenv('YOUTUBE_OPERATIONAL_API_URL')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
YT_UNOFFICAL_OR_UNKNOWN_ARTIST = 'YT_UNOFFICAL_OR_UNKNOWN_ARTIST'
UNOFFICAL_ARTIST_URI_STRING = 'DO_NOT_REFERENCE'

def clean_track_name(track_name:str) -> str:
    """
        Args:
            str: An unofficial track name
        Returns:
            str: Track title cleaned of common junk phrases
    """
    # Define a list of common junk phrases to remove from the track name
    junk_phrases = [
        'Official Music Video',
        'Official Video',
        'official video',
        'official music video',
        'OFFICIAL VIDEO',
        'Official Lyric Video',
        'Official 4K Video',
        'Official HD Video',
        '4K Remaster',
        'Remastered in 4K',
        'Offical Audio',
        'offical audio',
        'OFFICAL AUDIO',
        'Lyric Video',
        'Official Visualizer',
        '(MUSIC VIDEO)',
        '(Video)',
        '(OFFICIAL)',
        '(Official)',
        '(official)',
        '[HD]',
        '(HD)',
        '(4K)',
        '[4K]',
        '()',
        '[]'
    ]

    # Remove each junk phrase from the track name
    for phrase in junk_phrases:
        track_name = track_name.replace(phrase, '')

    # Strip any leading or trailing whitespace
    return track_name.strip()


class youtube_playlist_info(object):
    def __init__(self, id, user):
        self.id = id
        self.data = self.get_playlist_info()
        self.creating_user = user

    def get_paging(self, token):
        """Recursively fetches full track details from a paginated playlist endpoint."""
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=f'{self.id}',
            maxResults=50,
            pageToken=token
        ).execute()
        playlist_details = response
        track_ids = []

        # Function to extract track data
        def extract_track_data(track):
            if 'videoOwnerChannelId' in track['snippet']:
                print(track)
                video_id = track['contentDetails']['videoId']
                video_description = track['snippet']['description']
                desc_lines = video_description.split('\n')

                # check if description matches common format
                desc_auto_generated = (
                        desc_lines[0].startswith('Provided to YouTube by')
                        and desc_lines[len(desc_lines) - 1].startswith('Auto-generated by YouTube.')
                )

                # check if release date is in description
                date_in_desc = re.search(r'\d{4}-\d{2}-\d{2}', video_description)
                # api to see if video has music
                yt_operational_api_is_music = f"{YOUTUBE_OPERATIONAL_API_URL}/videos?part=music,explicitLyrics&id={video_id}"
                print(yt_operational_api_is_music)
                music_check_response = requests.get(yt_operational_api_is_music)
                print(music_check_response)
                if music_check_response.status_code == 200:
                    music_check_response = music_check_response.json()
                    print(music_check_response)
                    is_music = music_check_response['items'][0]['music']['available']
                    explicit = music_check_response['items'][0]['explicitLyrics']
                else:
                    raise ValueError('yt_operational_api is down')

                # if video is music or it is not sure, continue on
                if is_music or desc_auto_generated:
                    artist_channel_id = track['snippet']['videoOwnerChannelId']
                    # Get data from video in playlist
                    youtube_video = youtube.videos().list(
                        part="contentDetails, snippet",
                        id=f'{video_id}'
                    ).execute()

                    # assign
                    more_than_one_artist = False
                    video_duration = youtube_video['items'][0]['contentDetails']['duration']
                    duration = isodate.parse_duration(video_duration)
                    video_duration = int(duration.total_seconds() * 1000)

                    # assign release date to track
                    if date_in_desc and desc_auto_generated:
                        video_release = datetime.strptime(date_in_desc.group(), '%Y-%m-%d').date()
                    else:
                        video_release = None

                    artist_names = []
                    # assign album and artist name if track description is auto generated
                    if desc_auto_generated:
                        album_title = desc_lines[4].strip()  # album title is in 5th line of description
                        # remove - TOPIC from channel name if it is there.
                        artist_name = track['snippet']['videoOwnerChannelTitle'].replace(" - Topic", "")

                        extra_artist_names = desc_lines[2].split(" · ")
                        extra_artist_names = extra_artist_names[2:]
                        more_than_one_artist = len(extra_artist_names) > 0
                        if more_than_one_artist:
                            for item in extra_artist_names:
                                artist_names.append({
                                    "artist_name": item,
                                    "artist_youtube_uri": None,
                                    'offical': desc_auto_generated
                                })
                    else:
                        album_title = None
                        artist_name = YT_UNOFFICAL_OR_UNKNOWN_ARTIST

                    album_art_url = (
                        youtube_video['items'][0]['snippet']['thumbnails']['maxres']['url']
                        if 'maxres' in youtube_video['items'][0]['snippet']['thumbnails']
                        else youtube_video['items'][0]['snippet']['thumbnails']['default']['url']
                    )
                    track_data = {
                        'track_name': track['snippet']['title'] if desc_auto_generated else clean_track_name(track['snippet']['title']),
                        'track_id': video_id,
                        'duration_ms': video_duration,
                        'explicit': explicit,
                        'youtube_track_uri': track['contentDetails']['videoId'],
                        'youtube_album_uri': None,
                        'track_number': None,  # track['snippet']['position'],
                        'artists': {
                            'artist0':
                                {
                                    "artist_name": artist_name,
                                    "artist_youtube_uri": artist_channel_id if desc_auto_generated else None,
                                    'offical': desc_auto_generated
                                },
                        },
                        'album_art': album_art_url,
                        'album_name': album_title,
                        'release_date': video_release,
                        'offical_track': desc_auto_generated
                    }
                    if more_than_one_artist:
                        extra_artist_index = 1
                        for extra_artist in artist_names:
                            track_data['artists'][f'atrist{extra_artist_index}'] = extra_artist
                            extra_artist_index += 1
                    return track_data
                else:
                    return False
            else:
                return False

        # Extract track data for each track in the playlist
        tracks = playlist_details['items']
        tracks_skipped = 0
        for item in tracks:
            track = item
            track_exists = extract_track_data(track)
            if track and track_exists:  # Ensure the track details are present
                track_ids.append(track_exists)
            else:
                tracks_skipped + 1

        # Handle pagination if there are more tracks to fetch
        next_page = playlist_details['nextPageToken'] if 'nextPageToken' in playlist_details else None
        if next_page:
            track_ids.extend(self.get_paging(next_page))
        # pprint(track_ids)
        return track_ids

    def get_playlist_info(self):
        response = youtube.playlists().list(
            part="snippet,contentDetails",
            id=f'{self.id}'
        ).execute()
        playlist_details = response["items"][0]
        playlist_data = {'youtube_playlist_uri': playlist_details['id'],
                         'creator_name': playlist_details['snippet']['channelTitle'],
                         'playlist_name': playlist_details['snippet']['title'],
                         'playlist_description': playlist_details['snippet']['description'],
                         'playlist_image': playlist_details['snippet']['thumbnails']['default']['url'] if 'default' in
                                                                                                          playlist_details[
                                                                                                              'snippet'][
                                                                                                              'thumbnails'] else
                         playlist_details['snippet']['thumbnails']['maxres']['url'],
                         'total_tracks': playlist_details['contentDetails']['itemCount'],
                         'playlist_tracks': self.get_paging('')}
        return playlist_data

    def insert_playlist_db(self):
        playlist_data = self.data
        if not playlist_data['playlist_tracks']:
            raise ValueError('No music tracks found')
        # existing_playlist = Playlist.objects.filter(youtube_playlist_uri=playlist_data['youtube_playlist_uri']).first()
        # if existing_playlist:
        #     print(f"Playlist with Youtube ID {self.data['youtube_playlist_uri']} already exists.")
        #     # Optionally update existing_playlist here
        #     return existing_playlist.playlist_id

        # Continue with adding new playlist, tracks, and albums
        playlist_tracks = []
        dup_tracks = []
        for item in playlist_data['playlist_tracks']:
            print(item['artists'])
            artists = []
            for artist_key, artist_item in item['artists'].items():
                offical_artist = artist_item['offical']
                artist, _ = Artist.objects.get_or_create(
                    artist_name=artist_item['artist_name'],
                    defaults={
                        'youtube_music_channel_uri': artist_item[
                            'artist_youtube_uri'] if offical_artist else UNOFFICAL_ARTIST_URI_STRING,
                        'spotify_artist_uri': UNOFFICAL_ARTIST_URI_STRING if not offical_artist else None,
                        'apple_music_artist_uri': UNOFFICAL_ARTIST_URI_STRING if not offical_artist else None
                    }
                )
                if offical_artist:
                    if artist.youtube_music_channel_uri is None or artist.youtube_music_channel_uri == '':
                        artist.youtube_music_channel_uri = artist_item['artist_youtube_uri']
                        artist.save()
                print(artist)
                artists.append(artist)
            track_search = Track.objects.filter(
                track_name = item['track_name'],
                explicit= item['explicit'],
                album_title = item['album_name'],
                duration_ms_rounded = item['duration_ms'],
                offical_track = item['offical_track'],
                release_date = item['release_date'],
            )
            if len(track_search) == 2:
                first_track = track_search.first()
                last_track = track_search.last()

                if first_track.track_id != item['track_id'] and last_track.track_id == item['track_id']:
                    track = first_track
                    track_to_remove = last_track
                elif first_track.track_id == item['track_id'] and last_track.track_id != item['track_id']:
                    track = last_track
                    track_to_remove = first_track

                else:
                    track_to_remove = False
                    track_search = []
                if track_to_remove:
                    playlist_track_search = PlaylistTrack.objects.filter(
                        track=track_to_remove
                    )
                    for playlist_track in playlist_track_search:
                        playlist_search = Playlist.objects.filter(
                            tracks__in = [playlist_track]
                        )
                        for playlist in playlist_search:
                            updated_playlist_track, _ = PlaylistTrack.objects.get_or_create(
                                track = track,
                                playlist_position = playlist_track.playlist_position,
                                defaults={
                                    'track': track,
                                    'playlist_position': playlist_track.playlist_position
                                }
                            )
                            playlist.tracks.add(updated_playlist_track)
                            playlist.save()
                    dup_tracks.append(track_to_remove)
                    
            elif len(track_search) == 1:
                track = track_search.first()
            else:
                track, _ = Track.objects.get_or_create(
                        track_id = item['track_id'],
                        defaults = {
                        'track_id': item['track_id'],
                        'track_name':  item['track_name'],
                        'duration_ms_rounded':  item['duration_ms'],
                        'explicit':  item['explicit'],
                        'track_number':  item['track_number'],
                        'youtube_music_track_uri':  item['youtube_track_uri'],
                        'album_art_url':  item['album_art'],
                        'album_title':  item['album_name'],
                        'release_date': item['release_date'],
                        'original_platform':  'yt_music',
                        'offical_track': item['offical_track'],
                    }
                )
            if track.youtube_music_track_uri is None or track.youtube_music_track_uri == '':
                track.youtube_music_track_uri = item['youtube_track_uri']
                track.save()

            for artist in artists:
                track.artists.add(artist)
                track.save()

            playlist_tracks.append(track)

        playlist, _ = Playlist.objects.get_or_create(
            youtube_playlist_uri=playlist_data['youtube_playlist_uri'],
            playlist_track_length=len(playlist_tracks),
            playlist_image=playlist_data['playlist_image'],
            playlist_description=playlist_data['playlist_description'],
            user=self.creating_user,
            defaults={
                'playlist_name': playlist_data['playlist_name'],
                'user': self.creating_user,
                'playlist_description': playlist_data['playlist_description'],
                'playlist_track_length': len(playlist_tracks),  # Updated from 'total_tracks',
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

        for dup_track in dup_tracks:
            print(dup_track)
            dup_track.delete()
            
        print(f"Successfully added/updated playlist: {playlist.playlist_name}")
        return playlist.playlist_id