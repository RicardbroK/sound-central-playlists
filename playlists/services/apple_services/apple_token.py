from datetime import datetime, timedelta
import os
import jwt
from django.conf import settings
key =  os.getenv('APPLE_MUSIC_API_KEY').replace('\\n','\n' )
print(key)
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
    print(key)
    # Generate the JWT token
    token = jwt.encode(payload, key, algorithm='ES256',
                       headers=headers)

    return token