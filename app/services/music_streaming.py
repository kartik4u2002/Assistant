# music_streaming.py
import spotipy
from fastapi import HTTPException
from .spotify_auth import get_spotify_token

def get_spotify_client():
    token_info = get_spotify_token()
    if isinstance(token_info, dict) and 'access_token' in token_info:
        return spotipy.Spotify(auth=token_info['access_token'])
    else:
        raise HTTPException(status_code=401, detail="Spotify authentication required")

# music_streaming.py

def play_song(song_name, artist=None):
    try:
        sp = get_spotify_client()
        query = f"track:{song_name}"
        if artist:
            query += f" artist:{artist}"
        
        results = sp.search(q=query, limit=1, type='track')
        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            track_name = results['tracks']['items'][0]['name']
            artist_name = results['tracks']['items'][0]['artists'][0]['name']
            
            # Check if there's an active device
            devices = sp.devices()
            if not devices['devices']:
                return "No active Spotify devices found. Please open Spotify on a device."
            
            # Use the first available device
            device_id = devices['devices'][0]['id']
            
            sp.start_playback(device_id=device_id, uris=[track_uri])
            return f"Playing '{track_name}' by {artist_name}"
        return f"Song '{song_name}' not found"
    except spotipy.SpotifyException as e:
        if e.http_status == 404 and "NO_ACTIVE_DEVICE" in str(e):
            return "No active Spotify devices found. Please open Spotify on a device."
        raise HTTPException(status_code=e.http_status, detail=str(e))

def pause_song():
    try:
        sp = get_spotify_client()
        sp.pause_playback()
        return "Playback paused"
    except spotipy.SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))

def adjust_volume(volume_level):
    try:
        sp = get_spotify_client()
        sp.volume(volume_level)
        return f"Volume set to {volume_level}%"
    except spotipy.SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))