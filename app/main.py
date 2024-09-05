from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import RedirectResponse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import logging
from app.services.voice_recognition import recognize_speech
from app.services.command_parser import parse_command
from app.services.spotify_auth import get_spotify_token, play_spotify_song
import spotipy
import json 
from app.services.spotify_service import get_spotify_devices, play_song_on_spotify

# Initialize logging
logging.basicConfig(level=logging.INFO)
TOKEN_STORAGE_FILE = "token_info.json"

app = FastAPI(title="Music Assistant API")

# Load environment variables
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing user-library-read"

# Create SpotifyOAuth instance
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope
    )
@app.get("/")
async def root():
    return {"message": "Welcome to the Music Assistant API"}

@app.post("/voice-command")
async def process_voice_command(audio: UploadFile = File(...)):
    try:
        audio_data = await audio.read()
        recognized_text = recognize_speech(audio_data)
        logging.info(f"Recognized text: {recognized_text}")

        if recognized_text.startswith("Error"):
            logging.error(f"Recognition error: {recognized_text}")
            raise HTTPException(status_code=400, detail=recognized_text)

        command_response = parse_command(recognized_text)
        logging.info(f"Parsed command: {command_response}")

        if command_response.get("action") == "play":
            # Check if a valid token exists
            token_info = get_spotify_token()
            if not token_info:
                logging.error("No access token, redirecting to login.")
                return RedirectResponse(url="/login", status_code=302)
            
            # Get device associated with the user's account
            devices = get_spotify_devices(token_info['access_token'])
            if not devices or not isinstance(devices, list) or not all(isinstance(device, dict) for device in devices):
                return {"recognized_text": recognized_text, "response": "No devices Found"}
             
            # Proceed with playing the song if the token is valid
            device_id = devices[0].get('id')
            if not device_id:
                return {"recognized_text": recognized_text, "response": "No devices Found"}
            
            sp = spotipy.Spotify(auth=token_info['access_token'])
            song_name = command_response["song_name"]
            artist_name = command_response.get("artist_name")
            logging.info(f"Searching song: {song_name}, artist: {artist_name}")

            query = f"{song_name} artist:{artist_name}" if artist_name else song_name
            search_result = sp.search(q=query, type='track', limit=1)

            if search_result['tracks']['items']:
                track = search_result['tracks']['items'][0]
                track_uri = track['uri']

                sp_devices = sp.devices()
                if sp_devices and 'devices' in sp_devices and sp_devices['devices']:
                    device_id = sp_devices['devices'][0]['id']
                    logging.info(f"Playing song on device ID: {device_id}")
                    sp.start_playback(device_id=device_id, uris=[track_uri])
                    return {"recognized_text": recognized_text, "response": f"Playing {song_name} by {artist_name}"}
                else:
                    return {"recognized_text": recognized_text, "response": "No active Spotify devices found"}
            else:
                return {"recognized_text": recognized_text, "response": "Song not found"}

        return {"recognized_text": recognized_text, "response": command_response}

    except Exception as e:
        logging.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/login")
def login(request: Request):
    oauth = create_spotify_oauth()
    auth_url = oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    try:
        oauth = create_spotify_oauth()
        token_info = oauth.get_access_token(code)
        if not token_info:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        # Save the token for future use
        with open(TOKEN_STORAGE_FILE, 'w') as token_file:
            json.dump(token_info, token_file)
        
        # Redirect back to /voice-command or wherever you want after login
        return RedirectResponse("/spotify/devices")
    
    except Exception as e:
        logging.error(f"Error during Spotify callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in Spotify callback: {str(e)}")


@app.get("/spotify/devices")
def get_devices( access_token: str):
    return get_spotify_devices(access_token)

@app.get("/spotify-search")
async def search_spotify_track(query: str):
    try:
        token_info = get_spotify_token()
        if not token_info:
            logging.warning("No valid token found, redirecting to login.")
            return RedirectResponse(url="/login")

        sp = Spotify(auth=token_info)
        search_results = sp.search(q=query, type='track', limit=1)
        logging.info(f"Search results: {search_results}")
        return search_results
    
    except Exception as e:
        logging.error(f"Spotify search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Spotify search failed: {str(e)}")
@app.post("/play_song")
async def play_song(access_token: str, song_uri: str):
    devices = get_spotify_devices(access_token)
    if devices:
        device_id = devices[0].get('id')  # Select the first device
        response = play_song_on_spotify(access_token, device_id, song_uri)
        return {"message": "Song played successfully"}
    else:
        raise HTTPException(status_code=404, detail="No devices found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/sucess-page")
async def sucess_page():
    return{"message": "Login successful, you can now use voice commands!"}
@app.get("/health")
async def health_check():
    return {"status": "healthy"}





