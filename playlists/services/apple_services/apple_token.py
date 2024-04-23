from datetime import datetime, timedelta
import os
import jwt
from django.conf import settings

APPLE_MUSIC_API_KEY =  os.getenv('APPLE_MUSIC_API_KEY').replace('\\n','\n' )

def generate_apple_music_token():
    # Current time
    time_now = datetime.now()
    # Time when the token will expire
    time_expired = time_now + timedelta(hours=12)

    # Header with algorithm type and developer key
    headers = {
        "alg": 'ES256',
        "kid": os.getenv("APPLE_MUSIC_DEV_KEY")
    }

    # Payload with team ID, expiration time, and issued time
    payload = {
        "iss": os.getenv("APPLE_MUSIC_TEAM_ID"),
        "exp": int(time_expired.timestamp()),
        "iat": int(time_now.timestamp())
    }
    # Generate the JWT token
    token = jwt.encode(payload, APPLE_MUSIC_API_KEY, algorithm='ES256',
                       headers=headers)

    return token