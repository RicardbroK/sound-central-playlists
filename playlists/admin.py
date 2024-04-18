from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from django.contrib import admin
from .models import Artist, Track, Playlist


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['artist_id', 'artist_name', 'spotify_artist_uri', 'apple_music_artist_uri',
                    'youtube_music_channel_uri']
    ordering = ['artist_id', 'artist_name']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = [
        'track_id', 'album_title', 'album_art_url', 'track_name', 'duration_ms', 'explicit', 'release_date', 'spotify_track_uri',
        'apple_music_track_uri', 'youtube_music_track_uri', 'track_number', 'original_platform'
    ]
    ordering = ['track_id', 'track_name', 'album_title']
    search_fields = ['artists', 'track_name']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['playlist_id', 'playlist_name', 'playlist_description', 'playlist_track_length', 'created_at', 'updated_at', 'get_tracks_with_isrc']
    ordering = ['playlist_id', 'playlist_name']
    search_fields = ['playlist_name', 'tracks']

    def get_tracks_with_isrc(self, obj):
        # This method joins track names and their ISRCs, separated by a comma and a space
        # It uses line breaks in the admin view for better readability
        return format_html("<br>".join([f"{track.track_name} (ISRC: {track.track_id})" for track in obj.tracks.all()]))
    get_tracks_with_isrc.short_description = 'Tracks (with ISRC)'
