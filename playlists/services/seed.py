import json
from django.core.management.base import BaseCommand
from playlists.models import Artist, Album, Track


class Command(BaseCommand):
    help = 'Seeds the database with data from a JSON file'

    def handle(self, *args, **options):
        # Load JSON data
        with open('sample_playlist.json') as f:
            data = json.load(f)

        for item in data:
            for artist_data in item['artists']:
                artist, _ = Artist.objects.get_or_create(artist_name=artist_data['artist_name'])

            album, _ = Album.objects.get_or_create(
                album_name=item['album']['album_name'],
                release_date=item['album']['release_date'],
                total_tracks=item['album']['total_tracks']
            )

            track, _ = Track.objects.get_or_create(
                name=item['track_name'],
                duration_ms=item['duration_ms'],
                explicit=item['explicit'],
                track_number=item['track_number'],
                album_name=album
            )


