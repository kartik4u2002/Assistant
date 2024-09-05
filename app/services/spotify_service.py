import requests
from fastapi import HTTPException
import logging
import requests
from fastapi import HTTPException
from app.services.spotify_auth import log_request_response
import json

def play_song_on_spotify(access_token, device_id, song_uri):
    url = f"https://api.spotify.com/v1/me/player/play?device_id={device_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "uris": [song_uri]
    }

    response = log_request_response(url, method='PUT', headers=headers, data=json.dumps(payload))

    if isinstance(response, str):  # Check if response is a string
        logging.error(f"Error: {response}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    else:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="Premium required")
        elif response.status_code != 204:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    return response
# Other Spotify-related functions can go here


def get_spotify_devices(access_token: str):
    print(type(access_token))  # Print the type of access_token
    print(access_token)  # Print the contents of access_token

    url = "https://api.spotify.com/v1/me/player/devices"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    print(type(response))  # Print the type of response
    print(response)  # Print the contents of response

    if response.status_code == 200:
        print(type(response.json()))  # Print the type of response.json()
        print(response.json())  # Print the contents of response.json()
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())