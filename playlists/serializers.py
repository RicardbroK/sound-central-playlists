from rest_framework import serializers
from .models import Artist, Track, Genre, Playlist, PlaylistTrack


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['genre_id', 'genre_name']


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ['artist_id', 'artist_name', 'spotify_artist_uri', 'apple_music_artist_uri',
                  'youtube_music_channel_uri']

class TrackSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(many=True, read_only=True)  # Assuming a many-to-many relationship with Artist

    class Meta:
        model = Track
        fields = ['track_id', 'album_title', 'album_art_url', 'artists', 'track_name', 'duration_ms', 'explicit', 'release_date','spotify_track_uri',
                  'apple_music_track_uri', 'youtube_music_track_uri', 'track_number','original_platform', 'offical_track']
        
class PlayListTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer(many=False, read_only=True)  # Assuming a many-to-many relationship with Track

    class Meta:
        model = PlaylistTrack
        fields = ['track', 'playlist_position']

class PlaylistSerializer(serializers.ModelSerializer):
    tracks = PlayListTrackSerializer(many=True, read_only=True)  # Assuming a many-to-many relationship with Track

    class Meta:
        model = Playlist
        fields = ['playlist_id', 'user', 'fans', 'tracks', 'playlist_image', 'playlist_name', 'playlist_description', 'playlist_track_length',
                  'created_at', 'updated_at', 'youtube_playlist_uri', 'apple_playlist_uri', 'spotify_playlist_uri']