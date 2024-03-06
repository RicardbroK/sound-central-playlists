from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
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
    youtube_music_channel_uri = models.CharField(max_length=22,blank=True, default='', null=True) # Store YouTube Music URI for direct linking

    def __str__(self):
        return f"{self.artist_name}  (ID: {self.artist_id})"


class Album(models.Model):
    album_id = models.AutoField(primary_key=True)
    artists = models.ManyToManyField(Artist)
    album_name = models.CharField(max_length=255)
    album_art = models.URLField(blank=True, default='')  # Stores the album art from Spotify ATM
    release_date = models.DateField()
    total_tracks = models.IntegerField(blank=True, default=0)
    spotify_album_uri = models.CharField(max_length=22,blank=True, default='', null=True)  # Store Spotify URI for direct linking
    apple_music_album_uri = models.CharField(max_length=22,blank=True, default='', null=True) # Store Apple Music URI for direct linking
    youtube_music_album_uri = models.CharField(max_length=22,blank=True, default='', null=True) # Store YouTube Music URI for direct linking

    def __str__(self):
        return f"{self.album_name}"

    def save(self, *args, **kwargs):
        if isinstance(self.release_date, str):
            try:
                self.release_date = datetime.datetime.strptime(self.release_date, '%Y-%m-%d').date()
            except ValueError:
                try:
                    self.release_date = datetime.datetime.strptime(self.release_date, '%Y').date().replace(month=1,
                                                                                                           day=1)
                except ValueError:
                    raise ValidationError("Invalid date format. It must be in YYYY-MM-DD or YYYY format.")
        super(Album, self).save(*args, **kwargs)


class Track(models.Model):
    track_id = models.CharField(primary_key=True, max_length=12)
    album_id = models.ForeignKey(Album, on_delete=models.CASCADE)  # Link to Album
    artists = models.ManyToManyField(Artist)
    track_name = models.CharField(max_length=255)
    duration_ms = models.BigIntegerField(blank=True, default=0)
    explicit = models.BooleanField()
    spotify_track_uri = models.CharField(max_length=22,blank=True, default='', null=True) # Store Spotify URI for direct linking
    apple_music_track_uri = models.CharField(max_length=22,blank=True, default='', null=True)  # Store Apple Music URI for direct linking
    youtube_music_track_uri = models.CharField(max_length=22,blank=True, default='', null=True)  # Store YouTube Music URI for direct linking
    track_number = models.IntegerField(blank=True, default=1)

    def __str__(self):
        artist_names = ', '.join([artist.artist_name for artist in self.artists.all()])
        return f"{self.track_name} - {artist_names} (ID: {self.track_id})"


class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=255, blank=True, default='', null=True)
    tracks = models.ManyToManyField(Track)
    playlist_name = models.CharField(max_length=255)
    playlist_description = models.TextField(blank=True, default='')
    playlist_track_length = models.IntegerField(blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    spotify_playlist_uri = models.CharField(max_length=22,blank=True, default='', null=True)
    apple_playlist_uri = models.CharField(max_length=22,blank=True, default='', null=True)
    youtube_playlist_uri = models.CharField(max_length=22,blank=True, default='', null=True)

    # def __str__(self):
    #     return f"{self.playlist_name} - (ID: {self.playlist_id})"
