import re
import requests
from spotipy import Spotify
from app.services.spotify_auth import get_spotify_token
from app.services.spotify_service import play_song_on_spotify,get_spotify_devices
import os
import logging
import json
from requests import get
from fastapi import HTTPException 

def parse_command(text: str):
    text = text.lower()
    
    if text.startswith("play"):
        # Extract the song title and artist
        try:
            parts = text.split("by")
            song_name = parts[0].replace("play", "").strip()
            artist_name = parts[1].strip() if len(parts) > 1 else None
            return {"action": "play", "song_name": song_name, "artist_name": artist_name}
        except Exception as e:
            return {"error": f"Could not parse song name and artist: {str(e)}"}
    else:
        return {"error": "Command not recognized"}

def get_spotify_devices(access_token: str):
    url = "https://api.spotify.com/v1/me/player/devices"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        if isinstance(response_json, dict):
            return response_json
        else:
            raise HTTPException(status_code=500, detail="Invalid response from Spotify API")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    response = requests.get(url, headers=headers)
    print(response.text)  #

def get_track_uri(access_token, track_name, artist_name):
    url = "https://api.spotify.com/v1/search/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"q": f"track:{track_name} artist:{artist_name}"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        response_json = response.json()
        if 'tracks' in response_json and 'items' in response_json['tracks']:
            if response_json['tracks']['items']:
                track_uri = response_json['tracks']['items'][0]['uri']
                return track_uri
            else:
                raise HTTPException(status_code=404, detail="Track not found")
        else:
            raise HTTPException(status_code=404, detail="Track not found")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


def handle_voice_command():
    if os.path.exists('token.json'):
        logging.info("Token file found, attempting to retrieve token")
        with open('token.json') as f:
            token_info = json.load(f)
            logging.info(f"Token info: {token_info}")
            if isinstance(token_info, dict):
                access_token = token_info.get('access_token')
                if access_token:
                    device_id = get_spotify_devices  # retrieve device_id from somewhere
                    track_uri = get_track_uri  # retrieve track_uri from somewhere
                    play_song_on_spotify(access_token, device_id, track_uri)
                else:
                    logging.error("Access token not found in token info")
            else:
                logging.error("Token info is not a dictionary")
    else:
        logging.error("Token file not found")
        # handle error case
