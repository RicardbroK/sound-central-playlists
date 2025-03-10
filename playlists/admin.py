from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from django.contrib import admin
from .models import Artist, Track, Playlist, PlaylistTrack


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['artist_id', 'artist_name', 'spotify_artist_uri', 'apple_music_artist_uri',
                    'youtube_music_channel_uri']
    ordering = ['artist_id', 'artist_name']
    search_fields = ['artist_name', 'artist_id']

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = [
        'track_id', 'track_name', 'get_artist_names','album_title', 'album_art_url', 'duration_ms', 'duration_ms_rounded', 'explicit', 'release_date', 'spotify_track_uri',
        'apple_music_track_uri', 'youtube_music_track_uri', 'track_number', 'original_platform', 'offical_track'
    ]
    ordering = ['track_id', 'track_name', 'album_title']
    search_fields = ['artists__artist_name', 'track_name']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['playlist_id', 'playlist_name', 'playlist_description', 'playlist_track_length', 'created_at', 'updated_at', 'num_exports', 'get_num_fans','get_playlist_tracks']
    ordering = ['playlist_id', 'playlist_name', 'num_exports']
    search_fields = ['playlist_name', 'tracks__track__track_name']

@admin.register(PlaylistTrack)
class PlaylistTrackAdmin(admin.ModelAdmin):
    list_display = [
        'track', 'playlist_position'
    ]
    ordering = ['track', 'playlist_position']
    search_fields = ['track__track_name', 'track__artists__artist_name']

