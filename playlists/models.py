from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models


# # Create your models here.
# class User(AbstractUser):
#     """
#     User model to represent users who create playlists.
#     """
#
#     # Primary key field for unique user identification
#     user_id = models.AutoField(primary_key=True)
#
#     # Additional user information
#     username = models.CharField('username', max_length=100, unique=True)
#     password = models.CharField('password', max_length=100)  # Stored hashed
#     email = models.EmailField()
#     # String representation for displaying bettor information
#     def str(self):
#         return f'{self.username} - {self.user_id}'
#
#     # Override the save method to hash the password before saving
#     def save(self, args):
#         self.password = make_password(self.password)
#         super().save(args)

# Define the Genre model
class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
class Artist(models.Model):
    artist_id = models.AutoField(primary_key=True)
    artist_name = models.CharField(max_length=255)
    spotify_artist_uri = models.URLField(blank=True, default='')  # Store Spotify URI for direct linking
    apple_music_artist_uri = models.URLField(blank=True, default='')  # Store Apple Music URI for direct linking
    youtube_music_channel_uri = models.URLField(blank=True, default='')  # Store Youtube Music URI for direct linking

    def __str__(self):
        return f"{self.artist_name}  (ID: {self.artist_id})"


class Album(models.Model):
    album_id = models.AutoField(primary_key=True)
    artists = models.ManyToManyField(Artist)
    album_name = models.CharField(max_length=255)
    album_art = models.URLField(blank=True, default='') #Stores the album art from Spotify ATM
    release_date = models.DateField()
    total_tracks = models.IntegerField(blank=True, default=0)
    spotify_album_uri = models.URLField(blank=True, default='')  # Store Spotify URI for direct linking
    apple_music_album_uri = models.URLField(blank=True, default='')  # Store Apple Music URI for direct linking
    youtube_music_album_uri = models.URLField(blank=True, default='')  # Store YouTube Music URI for direct linking

    def __str__(self):
        return f"{self.album_name} - (ID: {self.album_id})"


# linking table for artists and albums

class Track(models.Model):
    track_id = models.CharField(primary_key=True , length=12)
    album_id = models.ForeignKey(Album, on_delete=models.CASCADE)  # Link to Album
    artists = models.ManyToManyField(Artist)
    track_name = models.CharField(max_length=255)
    duration_ms = models.IntegerField(blank=True, default=0)
    explicit = models.BooleanField()
    spotify_track_uri = models.URLField(blank=True, default='')  # Store Spotify URI for direct linking
    apple_music_track_uri = models.URLField(blank=True, default='')  # Store Apple Music URI for direct linking
    youtube_music_track_uri = models.URLField(blank=True, default='')  # Store YouTube Music URI for direct linking
    track_number = models.IntegerField(blank=True, default=1)
    # genres = models.ManyToManyField(Genre, related_name='tracks')  # Many-to-many relationship to Genre
    def __str__(self):
        # Modified to handle multiple artists
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

    # You can add more fields here as needed, such as a description or an owner

    def __str__(self):
        return f"{self.playlist_name} (ID: {self.playlist_id})"
