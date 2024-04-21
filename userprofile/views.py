from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import json
from django.shortcuts import redirect
import os
from datetime import datetime
from playlists.services.spotify_services import spotfiy_extra_services
from spotipy import SpotifyOAuth

SPOTIFY_CLIENT=os.getenv('SPOTIPY_CLIENT_ID')
SPOTIFY_SECRET=os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIFY_REDIRECT=os.getenv('SPOTIPY_REDIRECT_URI')

# Create your views here.
def viewprofile(request):
   return HttpResponse('This will be url to manage user profile')

def spotify_oauth(request):
   spotify_session = request.session.get('spotify')
   present_date = datetime.now()
   timestamp = int(datetime.timestamp(present_date))
   sp_auth = SpotifyOAuth(
        # Your Spotify API credentials
        client_id=SPOTIFY_CLIENT,
        client_secret=SPOTIFY_SECRET,
        redirect_uri=SPOTIFY_REDIRECT,
        scope=['user-read-email','user-read-private','user-library-read', 'user-library-modify', 'playlist-modify-public', 'playlist-modify-private']  # Specify required scopes
    )
   if spotify_session is None:
      auth_url = sp_auth.get_authorize_url()
      return redirect(auth_url)
   if 'expires_at' in spotify_session:
      if timestamp > spotify_session['expires_at']:
         if 'refresh_token' in spotify_session:
            try:
               request.session['spotify'] = spotfiy_extra_services.refresh_spotify_token(spotify_session['refresh_token'])
               return redirect(request, 'spotify_callback')
            except:
               auth_url = sp_auth.get_authorize_url()
               return redirect(auth_url)
      else:
         return redirect(request, 'spotify_callback')
   auth_url = sp_auth.get_authorize_url()
   return redirect(auth_url)

# Handle the callback after user authorization
def spotify_callback(request):
   page_to_render = render(request, 'callbacks/callback.html')
   code = request.GET.get('code')
   if code is not None:
      sp_auth = SpotifyOAuth(
         client_id=SPOTIFY_CLIENT,
         client_secret=SPOTIFY_SECRET,
         redirect_uri=SPOTIFY_REDIRECT
      )
      token_info = sp_auth.get_access_token(code)
      print(token_info)
      #page_to_render = HttpResponse('Please close this window.')
      request.session['spotify'] = token_info
   return page_to_render