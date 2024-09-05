import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from fastapi.responses import RedirectResponse
import requests  # Ensure you have this import for logging requests

# Set up logging
logging.basicConfig(level=logging.INFO)

# Path to the file where tokens are stored
TOKEN_STORAGE_FILE = "token_info.json"

scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"

def create_spotify_oauth():
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope
    )

def get_spotify_token():
    if os.path.exists(TOKEN_STORAGE_FILE):
        logging.info("Token file found, attempting to retrieve token")
        try:
            with open(TOKEN_STORAGE_FILE, 'r') as token_file:
                token_info = json.load(token_file)
        except json.JSONDecodeError:
            logging.error("Invalid JSON in token file, deleting file")
            os.remove(TOKEN_STORAGE_FILE)
            return None

        # Check if token is expired and refresh if necessary
        oauth = create_spotify_oauth()
        if oauth.is_token_expired(token_info):
            logging.info("Token expired, attempting to refresh")
            try:
                token_info = oauth.refresh_access_token(token_info['refresh_token'])
                logging.info("Token refreshed successfully")
            except Exception as e:
                logging.error(f"Error refreshing token: {str(e)}")
                return None

            # Save refreshed token
            with open(TOKEN_STORAGE_FILE, 'w') as token_file:
                json.dump(token_info, token_file)

        return token_info['access_token']

    # If no token, return None, and handle redirection in the calling function
    logging.warning("No token found, redirecting to login.")
    return None


def log_request_response(url, method, headers, data):
    response = requests.request(method, url, headers=headers, data=data)
    logging.info(f"Request: {method} {url}")
    logging.info(f"Headers: {headers}")
    logging.info(f"Data: {data}")
    logging.info(f"Response: {response.text}")
    return response


def play_spotify_song(access_token, song_name, artist_name=None):
    try:
        sp = spotipy.Spotify(auth=access_token)

        if artist_name:
            logging.info(f"Searching for song: {song_name} by {artist_name}")
            query = f"{song_name} artist:{artist_name}"
        else:
            logging.info(f"Searching for song: {song_name}")
            query = song_name

        # Log the search request
        log_request_response(f"https://api.spotify.com/v1/search?q={query}&type=track", method='GET', headers={'Authorization': f'Bearer {access_token}'})

        results = sp.search(q=query, type='track')

        if results['tracks']['total'] > 0:
            track_uri = results['tracks']['items'][0]['uri']
            logging.info(f"Track found: {track_uri}")
            
            devices = sp.devices()
            logging.info(f"Devices found: {devices}")

            if devices['devices']:
                device_id = devices['devices'][0]['id']
                logging.info(f"Playing on device: {device_id}")
                sp.start_playback(device_id=device_id, uris=[track_uri])
            else:
                logging.warning("No active Spotify devices found.")
                raise Exception("No active Spotify devices found.")
        else:
            logging.warning(f"Song not found: {song_name} by {artist_name}")
            raise Exception(f"Song not found: {song_name} by {artist_name}")

    except Exception as e:
        logging.error(f"Error in play_spotify_song: {str(e)}")
        raise e
