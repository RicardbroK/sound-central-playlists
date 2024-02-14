from rest_framework import serializers
from .models import Artist, Album, Track, Playlist, Genre
from rest_framework.authtoken.admin import User


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['user_id', 'username', 'email', 'password']

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['genre_id', 'name']


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ['artist_id', 'artist_name', 'spotify_artist_uri', 'apple_music_artist_uri',
                  'youtube_music_channel_uri']


class AlbumSerializer(serializers.ModelSerializer):
    artist_id = ArtistSerializer(many=True, read_only=True)  # Assuming a many-to-many relationship with Artist

    class Meta:
        model = Album
        fields = ['album_id', 'artists', 'album_name', 'album_art', 'release_date', 'total_tracks', 'spotify_album_uri',
                  'apple_music_album_uri', 'youtube_music_album_uri']


class TrackSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(many=True, read_only=True)  # Assuming a many-to-many relationship with Artist

    class Meta:
        model = Track
        fields = ['track_id', 'album_id', 'artists', 'track_name', 'duration_ms', 'explicit', 'spotify_track_uri',
                  'apple_music_track_uri', 'youtube_music_track_uri', 'track_number']


class PlaylistSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True, read_only=True)  # Assuming a many-to-many relationship with Track

    class Meta:
        model = Playlist
        fields = ['playlist_id', 'tracks', 'playlist_name', 'playlist_description',
                  'playlist_track_length', 'created_at', 'updated_at']
