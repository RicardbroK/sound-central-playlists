import json
from datetime import datetime
from django.core.management.base import BaseCommand
from playlists.models import Artist, Album, Track

class Command(BaseCommand):
    help = 'Seeds the database with data from a JSON file'

    def handle(self, *args, **options):
        # Load JSON data
        with open('sample_playlist.json') as f:
            data = json.load(f)

        for item in data:
            # Validate release_date format
            try:
                release_date = datetime.strptime(item['release_date'], "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date format for album {item['album_id']}: {item['release_date']}")
                continue  # Skip this album if the release_date is invalid

            # Get or create Album
            album, _ = Album.objects.get_or_create(
                album_id=item['album_id'],
                defaults={
                    'album_name': item['album_name'],
                    'release_date': release_date,
                    'total_tracks': int(item['album_total_tracks']),
                    'album_art': item['album_art'],
                    'spotify_album_uri': item['spotify_album_uri']
                }
            )

            # Get or create Track
            track, created = Track.objects.get_or_create(
                track_id=item['track_id'],
                defaults={
                    'track_name': item['track_name'],
                    'duration_ms': int(item['duration_ms']),
                    'explicit': item['explicit'],
                    'track_number': int(item['track_number']),
                    'album': album,
                    'spotify_track_uri': item['spotify_track_uri'],
                }
            )

            # Only add artists if track was created to avoid duplicating artist-track associations
            if created:
                for artist_name in item['artists_names']:
                    artist, _ = Artist.objects.get_or_create(artist_name=artist_name,
                                                             )
                    track.artists.add(artist)
