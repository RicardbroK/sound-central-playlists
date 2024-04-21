#Authored by Ricardo Kifuri
#kifuriricardo@gmail.com
import requests
import os
from datetime import datetime
from typing import Union
import urllib.parse

def refresh_spotify_token(refresh_token:str) -> str:
    """
    Refreshes the Spotify access token using the provided refresh token.
    Args:
        refresh_token (str): The refresh token obtained during initial authorization.
    Returns:
        str: The spotify response in JSON format
    """
    url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': os.getenv('SPOTIPY_CLIENT_ID'),
        'client_secret': os.getenv('SPOTIPY_CLIENT_SECRET')
    }

    response = requests.post(url, data=payload)
    data = response.json()
    present_date = datetime.now()
    timestamp = int(datetime.timestamp(present_date))
    if 'access_token' in data:
        data['expires_at'] = timestamp + data['expires_in']
        return data
    else:
        raise Exception(f"Error refreshing token: {data.get('error_description', 'Unknown error')}")
    
def search_spotify_uri(track:dict, accuss_token:str) -> Union[str, bool]:
            """
                Searches for the Spotify URI of a given track.

                Args:
                    track (dict): A dictionary containing track information.
                    accuss_token (str): Spotify access token.

                Returns:
                    str: The Spotify URI of the track.
                    bool: False if could not be found
            """
            TRACK_SEARCH_LIMIT = 1
            SPOTIFY_URL_START = 'https://api.spotify.com/v1/search?q='
            SPOTIFY_URL_END = f'&type=track&limit={TRACK_SEARCH_LIMIT}'
            spotify_token = accuss_token
            if track['spotify_track_uri'] == '' or track['spotify_track_uri'] is None:
                # If the Spotify URI is missing, search for it
                track_name = track['track_name']
                if track['offical_track'] and track['original_platform'] != 'yt_music':
                    # If it's an official track and not from YouTube Music, search by ISRC
                    isrc = track['track_id']
                    endpoint = f'{SPOTIFY_URL_START}isrc%3A{isrc}{SPOTIFY_URL_END}'
                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                    response = requests.get(endpoint, headers=header)
                    print(response.content)
                    try:
                        return response.json()['tracks']['items'][0]['uri']
                    except:
                        print('Offical track, ISRC not found, finding alternative.')
                        artist = track['artists'][0]['artist_name']
                        track_name = track['track_name']
                        track_album_title = track['album_title']
                        # Search by track name, artist, and album
                        searchterms=  urllib.parse.quote(f'{track_name} {artist} artist:{artist} album:{track_album_title}').replace('%20', '+')
                        endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                        header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                        response = requests.get(endpoint, headers=header)
                        print(response.status_code)
                        if response.status_code == 200:
                            try:
                                return response.json()['tracks']['items'][0]['uri']
                            except Exception as e:
                                print(response.content)
                                print('Second search failed.')
                                try:
                                    # If the second search fails, search by track name and artist only
                                    searchterms= urllib.parse.quote(f'q={track_name} {artist} artist:{artist}').replace('%20', '+')
                                    endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                                    response = requests.get(endpoint, headers=header)
                                    return response.json()['tracks']['items'][0]['uri']
                                except:
                                    print(response.content)
                                    print('Final search failed, skipping.')
                                    return False # Return False if all searches fail
                        else:
                            print(response.content)
                            print(track_name)
                            print(endpoint)
                            print('Track skipped.')
                            return False # Return False if first response fails
                        
                elif track['offical_track']:
                    # If it's an official track and from YouTube Music, search by search by track name, artist, and album
                    artist = track['artists'][0]['artist_name']
                    track_album_title = track['album_title']
                    # Search by track name, artist, and album
                    searchterms= urllib.parse.quote(f'{track_name} {artist} artist:{artist} album:{track_album_title}').replace('%20', '+')
                    endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                    response = requests.get(endpoint, headers=header)
                    print(response.status_code)
                    if response.status_code == 200:
                        try:
                            return response.json()['tracks']['items'][0]['uri']
                        except Exception as e:
                            print(response.content)
                            print('First search failed.')
                            try:
                                # If the first search fails, search by track name and artist only
                                searchterms= urllib.parse.quote(f'{track_name} {artist} artist:{artist}').replace('%20', '+')
                                endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                                header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                                response = requests.get(endpoint, headers=header)
                                return response.json()['tracks']['items'][0]['uri']
                            except:
                                print(response.content)
                                print('Final search failed, skipping.')
                                return False  # Return False if all searches fail
                    else:
                        print(response.content)
                        print(track_name)
                        print(endpoint)
                        print('Track skipped.')
                        return False # Return False if first response fails
                else:
                    # If track not official, search only by title
                    searchterms= urllib.parse.quote(f'{track_name}').replace('%20', '+')
                    endpoint = SPOTIFY_URL_START+searchterms+SPOTIFY_URL_END
                    header = {'Authorization': 'Bearer'+f' {spotify_token}'}
                    response = requests.get(endpoint, headers=header)
                    print(response.status_code)
                    if response.status_code == 200:
                        try:
                            return response.json()['tracks']['items'][0]['uri']
                        except Exception as e:
                            print('Unofficial track, no track found, skipping.')
                            return False # Return False if search fails
                    else:
                        print(response.content)
                        print(track_name)
                        print(endpoint)
                        print('Track skipped.')
                        return False # Return False if first response fails
            else:
                # If the Spotify URI is already provided, return it
                return 'spotify:track:'+track['spotify_track_uri']