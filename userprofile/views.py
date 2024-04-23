from django.shortcuts import render, redirect
from django.http import HttpResponse
import os
from datetime import datetime
from playlists.services.spotify_services import spotfiy_extra_services
from django.http import QueryDict
import random
import string
import requests
import base64

SPOTIFY_CLIENT=os.getenv('SPOTIPY_CLIENT_ID')
SPOTIFY_SECRET=os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIFY_REDIRECT=os.getenv('SPOTIPY_REDIRECT_URI')

# Create your views here.
def viewprofile(request):
   return HttpResponse('This will be url to manage user profile')

def spotify_oauth(request) -> redirect:
   """
   View for initiating Spotify OAuth authentication.

   Args:
       request: Django HTTP request object.

   Returns:
       Redirects to Spotify authorization URL or callback view.

   Notes:
       - Generates a random state string for CSRF protection.
       - If a valid Spotify session exists, checks token expiration and refreshes if necessary.
       - Redirects to the Spotify authorization URL if no session or expired session.
   """
   # Get the existing Spotify session from the user's session
   spotify_session = request.session.get('spotify')

   # Get the current timestamp
   present_date = datetime.now()
   timestamp = int(datetime.timestamp(present_date))

   def generate_random_string(length: int) -> str:
      """
      Generates a random string of specified length.

      Args:
         length: Length of the random string.

      Returns:
         Random string containing alphanumeric characters.
      """
      characters = string.ascii_letters + string.digits
      return ''.join(random.choice(characters) for _ in range(length))

   # Define the required Spotify OAuth scope
   scope = ['user-read-email', 'user-read-private', 'user-library-read', 'user-library-modify',
            'playlist-modify-public', 'playlist-modify-private']
   separator = "%20"

   # Generate a random state string for CSRF protection
   spotify_state = generate_random_string(16)

   # Construct the Spotify authorization URL
   auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={SPOTIFY_CLIENT}" \
               f"&redirect_uri={SPOTIFY_REDIRECT}&scope={separator.join(scope)}&state={spotify_state}"

   # If no Spotify session exists, store the state and redirect to the authorization URL
   if spotify_session is None:
      request.session['spotify-state'] = spotify_state
      return redirect(auth_url)

   # Check if the session has an 'expires_at' timestamp
   if 'expires_at' in spotify_session:
      # If the token has expired, attempt to refresh it
      if timestamp > spotify_session['expires_at']:
         if 'refresh_token' in spotify_session:
            try:
               # Refresh the Spotify token
               request.session['spotify'] = spotfiy_extra_services.refresh_spotify_token(
                  spotify_session['refresh_token'])
               return redirect('spotify_callback')
            except Exception as e:
               print(e)
               # If refresh fails, store the new state and redirect to the authorization URL
               request.session['spotify-state'] = spotify_state
               return redirect(auth_url)
      else:
         # If token is still valid, redirect to the callback view
         return redirect('spotify_callback')

   # Store the new state and print the authorization URL
   request.session['spotify-state'] = spotify_state
   print(auth_url)
   return redirect(auth_url)

# Handle the callback after user authorization
def spotify_callback(request) -> HttpResponse:
   """
   Callback view for Spotify authentication.

   Args:
      request: Django HTTP request object.

   Returns:
      page_to_render: Rendered HTML page for the callback.

   Raises:
      ValueError: If 'code' parameter is missing or if 'state' parameter does not match the session state.
      Exception: If there is an error during the Spotify authentication process.
   """
   # Render the callback HTML page
   page_to_render = render(request, 'callbacks/callback.html')
   try:
      # Get the 'code' parameter from the query string
      code = request.GET.get('code')
      if code is None:
         raise ValueError('No code provided')

      # Get the 'state' parameter from the query string
      state = request.GET.get('state')
      if state != request.session.get('spotify-state'):
         raise ValueError('State provided does not match')

      # Spotify API endpoint for token exchange
      endpoint = 'https://accounts.spotify.com/api/token'

      # Create a string to encode for Basic Authorization
      string_to_encode = f"{SPOTIFY_CLIENT}:{SPOTIFY_SECRET}"
      byte_type_string = f"{string_to_encode}".encode("utf-8")

      # Set the headers for the token exchange request
      header = {
            'content-type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(byte_type_string).decode("utf-8")
      }

      # Set the data for the token exchange request
      data = {
         'code': code,
         'redirect_uri': SPOTIFY_REDIRECT,
         'grant_type': "authorization_code",
      }

      # Make a POST request to exchange the authorization code for an access token
      response = requests.post(url=endpoint, headers=header, data=data)
      token_info = response.json()

      # Check if the access token is present in the response
      if 'access_token' in token_info:
         # Get the current timestamp
         present_date = datetime.now()
         timestamp = int(datetime.timestamp(present_date))
         token_info['expires_at'] = timestamp + token_info['expires_in']
         request.session['spotify'] = token_info
      else:
         raise Exception(f'No access token in response: {token_info}')

   except Exception as e:
      # Handle exceptions and set status code to 400
         print(e)
         page_to_render.status_code = 400
   return page_to_render