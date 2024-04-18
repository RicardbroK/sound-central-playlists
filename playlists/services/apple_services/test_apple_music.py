import os
import datetime
import jwt
import cryptography
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
# set up the authentication for Apple Music using dev token


# requires pyjwt (https://pyjwt.readthedocs.io/en/latest/)
# pip install pyjwt


APPLE_MUSIC_API_KEY = os.getenv("APPLE_MUSIC_API_KEY")
APPLE_MUSIC_TEAM_ID = os.getenv("APPLE_MUSIC_TEAM_ID")
APPLE_MUSIC_DEV_KEY = os.getenv("APPLE_MUSIC_DEV_KEY")
alg = 'ES256'

time_now = datetime.datetime.now()
time_expired = datetime.datetime.now() + datetime.timedelta(hours=12)
headers = {
    "alg": alg,
    "kid": str(APPLE_MUSIC_DEV_KEY)
}

payload = {
    "iss": APPLE_MUSIC_TEAM_ID,
    "exp": int(time_expired.timestamp()),  # Changed to use .timestamp() method
    "iat": int(time_now.timestamp())  # Changed to use .timestamp() method
}
if __name__ == "__main__":
    """Create an auth token"""
    token = jwt.encode(payload, APPLE_MUSIC_API_KEY, algorithm=alg, headers=headers)

    url = "https://api.music.apple.com/v1/catalog/us/playlists/pl.14362d3dfe4b41f7878939782647e0ba"

    print("curl -v -H 'Authorization: Bearer " + token + " " + "\"" + url + "\"")
    print(token)
    # request_obj = requests.get(url, headers={'Authorization': "Bearer " + token})
    # json_dict = request_obj.json()