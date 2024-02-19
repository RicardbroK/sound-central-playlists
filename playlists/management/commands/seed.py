import json
from datetime import datetime
from django.core.management.base import BaseCommand
from playlists.models import Artist, Album, Track


class Command(BaseCommand):
    help = 'Seeds the database with data from a JSON file'

    def handle(self, *args, **options):
        with open('sample_playlist.json') as f:
            data = json.load(f)

        for item in data:
            try:
                release_date = datetime.strptime(item['release_date'], "%Y-%m-%d")
            except ValueError:
                # Extract year from the provided date string
                year = item['release_date'].split("-")[0]
                # Set release date to January 1st of the extracted year
                release_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")

            album, _ = Album.objects.get_or_create(
                spotify_album_uri=item['spotify_album_uri'],
                defaults={
                    'album_name': item['album_name'],
                    'release_date': release_date,
                    'total_tracks': int(item['album_total_tracks']),
                    'album_art': item['album_art'],
                }
            )

            track, created = Track.objects.get_or_create(
                track_id=item['track_id'],
                defaults={
                    'track_name': item['track_name'],
                    'duration_ms': int(item['duration_ms']),
                    'explicit': item['explicit'],
                    'track_number': int(item['track_number']),
                    'album_id': album,
                    'spotify_track_uri': item['spotify_track_uri'],
                }
            )

            if created:
                for artist_key, artist_value in item['artists'].items():
                    artist, _ = Artist.objects.get_or_create(
                        artist_name=artist_value['artist_name'],
                        defaults={'spotify_artist_uri': artist_value['artist_spotify_uri']}
                    )
                    track.artists.add(artist)
