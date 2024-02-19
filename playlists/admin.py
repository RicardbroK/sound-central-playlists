from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Artist, Album, Track, Playlist


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['artist_id', 'artist_name', 'spotify_artist_uri', 'apple_music_artist_uri',
                    'youtube_music_channel_uri']
    ordering = ['artist_id', 'artist_name']


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['album_id', 'album_name', 'release_date', 'total_tracks', 'spotify_album_uri',
                    'apple_music_album_uri', 'youtube_music_album_uri']
    ordering = ['album_id', 'album_name', 'release_date']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = [
        'track_id', 'album_id', 'track_name', 'duration_ms', 'explicit', 'spotify_track_uri',
        'apple_music_track_uri', 'youtube_music_track_uri', 'track_number'
    ]
    ordering = ['track_id', 'track_name', 'album_id']
    search_fields = ['artists', 'track_name']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['playlist_id', 'playlist_name', 'playlist_description',
                    'playlist_track_length', 'created_at', 'updated_at']
    ordering = ['playlist_id', 'playlist_name']
    search_fields = ['playlist_name', 'tracks']
