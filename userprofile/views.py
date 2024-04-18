from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import json
from django.shortcuts import redirect
import os
from http.cookies import SimpleCookie
from spotipy import SpotifyOAuth

SPOTIFY_CLIENT=os.getenv('SPOTIPY_CLIENT_ID')
SPOTIFY_SECRET=os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIFY_REDIRECT=os.getenv('SPOTIPY_REDIRECT_URI')

# Create your views here.
def viewprofile(request):
   return HttpResponse('This will be url to manage user profile')

def spotify_oauth(request):
    sp_auth = SpotifyOAuth(
        # Your Spotify API credentials
        client_id=SPOTIFY_CLIENT,
        client_secret=SPOTIFY_SECRET,
        redirect_uri=SPOTIFY_REDIRECT,
        scope=['user-read-email','user-read-private','user-library-read', 'user-library-modify', 'playlist-modify-public', 'playlist-modify-private']  # Specify required scopes
    )
    auth_url = sp_auth.get_authorize_url()
    return redirect(auth_url)

# Handle the callback after user authorization
def spotify_callback(request):
   sp_auth = SpotifyOAuth(
      client_id=SPOTIFY_CLIENT,
      client_secret=SPOTIFY_SECRET,
      redirect_uri=SPOTIFY_REDIRECT
   )
   code = request.GET.get('code')
   token_info = sp_auth.get_access_token(code)
   max_age = token_info['expires_in']
   token_info = json.dumps(token_info)
   print(token_info)
   #page_to_render = HttpResponse('Please close this window.')
   page_to_render = render(request, 'callbacks/callback.html')
   request.session['spotify'] = token_info
   return page_to_render