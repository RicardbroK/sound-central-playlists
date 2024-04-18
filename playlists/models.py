from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
import datetime

class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    genre_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.genre_name

class Artist(models.Model):
    artist_id = models.AutoField(primary_key=True)
    artist_name = models.CharField(max_length=255)
    spotify_artist_uri = models.CharField(max_length=22,blank=True, default='', null=True)  # Store Spotify URI for direct linking
    apple_music_artist_uri = models.CharField(max_length=22,blank=True, default='', null=True)# Store Apple Music URI for direct linking
    youtube_music_channel_uri = models.CharField(max_length=55,blank=True, default='', null=True) # Store YouTube Music URI for direct linking

    def __str__(self):
        return f"{self.artist_name}  (ID: {self.artist_id})"

class Track(models.Model):
    track_id = models.CharField(primary_key=True, max_length=22)
    album_title = models.CharField(max_length=255,blank=True, default='', null=True)
    album_art_url = models.URLField(blank=True, default='', max_length=2000)  # Stores the album art from Spotify ATM
    artists = models.ManyToManyField(Artist)
    track_name = models.CharField(max_length=255)
    duration_ms = models.BigIntegerField(blank=True, null=True)
    duration_ms_rounded = models.BigIntegerField(blank=True, default=0)
    explicit = models.BooleanField(null=True)
    release_date = models.DateField(null=True)
    spotify_track_uri = models.CharField(max_length=22,blank=True, default='', null=True) # Store Spotify URI for direct linking
    apple_music_track_uri = models.CharField(max_length=22,blank=True, default='', null=True)  # Store Apple Music URI for direct linking
    youtube_music_track_uri = models.CharField(max_length=55,blank=True, default='', null=True)  # Store YouTube Music URI for direct linking
    track_number = models.IntegerField(blank=True, default=1, null=True)
    offical_track = models.BooleanField(null=True)
    original_platform = models.CharField(max_length=10, default='')

    def __str__(self):
        artist_names = ', '.join([artist.artist_name for artist in self.artists.all()])
        return f"{self.track_name} - {artist_names} (ID: {self.track_id})"


class PlaylistTrack(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, null = False)
    playlist_position = models.IntegerField(null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['track', 'playlist_position'], name='unique_track_posistion'
            )
        ]

    def __str__(self):
        return f"Track [{self.track.track_name}] - (Position: {self.playlist_position})"

class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='creator', null=True, default=None)
    fans = models.ManyToManyField(settings.AUTH_USER_MODEL)
    playlist_name = models.CharField(max_length=255)
    playlist_description = models.TextField(blank=True, default='')
    playlist_image = models.URLField(max_length=2000, null=True)
    tracks = models.ManyToManyField(PlaylistTrack)
    playlist_track_length = models.IntegerField(blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    spotify_playlist_uri = models.CharField(max_length=22,blank=True, default='', null=True)
    apple_playlist_uri = models.CharField(max_length=22,blank=True, default='', null=True)
    youtube_playlist_uri = models.CharField(max_length=55,blank=True, default='', null=True)

    def __str__(self):
        return f"{self.playlist_name} - (ID: {self.playlist_id})"