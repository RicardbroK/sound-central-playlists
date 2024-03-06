import json
from datetime import datetime
from django.core.management.base import BaseCommand
from playlists.models import Artist, Album, Track, Playlist


class Command(BaseCommand):
    help = 'Seeds the database with data from a JSON file'

    def handle(self, *args, **options):
        with open('playlist_details.json') as f:
            data = json.load(f)
        playlist_tracks = []
        for item in data[0]['playlist_tracks']:
            try:
                release_date = datetime.strptime(item['release_date'], "%Y-%m-%d")
            except ValueError:
                # Extract year from the provided date string
                year = item['release_date'].split("-")[0]
                # Set release date to January 1st of the extracted year
                release_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")
            artists = []
            for artist_key, artist_value in item['artists'].items():
                artist = Artist.objects.get_or_create(
                    artist_name=artist_value['artist_name'],
                    spotify_artist_uri=artist_value['artist_spotify_uri']
                )
                artists.append(artist[0].artist_id)

            album, _ = Album.objects.get_or_create(
                spotify_album_uri=item['spotify_album_uri'],
                album_name=item['album_name'],
                release_date=release_date,
                total_tracks=int(item['album_total_tracks']),
                album_art=item['album_art'],
            )
            for artist_id in artists:
                album.artists.add(artist_id)

            track, _ = Track.objects.get_or_create(
                track_id=item['track_id'],
                track_name=item['track_name'],
                duration_ms=int(item['duration_ms']),
                explicit=item['explicit'],
                track_number=int(item['track_number']),
                album_id=album,
                spotify_track_uri=item['spotify_track_uri'],
            )
            for artist_id in artists:
                track.artists.add(artist_id)
            playlist_tracks.append(track.track_id)

        playlist, _ = Playlist.objects.get_or_create(
            spotify_playlist_uri=data[0]['spotify_playlist_id'],
            playlist_name=data[0]['playlist_name'],
            playlist_description=data[0]['playlist_description'],
            #total_tracks=int(data[0]['total_tracks']),
            #playlist_image=data[0]['playlist_image'],
        )
        for track in playlist_tracks:
            playlist.tracks.add(track)
