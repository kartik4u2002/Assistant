import speech_recognition as sr
import logging
from io import BytesIO

# Initialize the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def recognize_speech(audio_data):
    recognizer = sr.Recognizer()

    try:
        # Convert raw audio data (bytes) into a file-like object using BytesIO
        audio_file = BytesIO(audio_data)
        
        # Use sr.AudioFile for better handling of various formats
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source)  # Adjust for background noise
            audio_data = recognizer.record(source)  # Record the audio from the file

        text = recognizer.recognize_google(audio_data)
        logger.info(f"Recognized text: {text}")
        return text

    except sr.UnknownValueError:
        logger.warning("Speech recognition could not understand the audio")
        return "Speech recognition could not understand the audio"
    except sr.RequestError as e:
        logger.error(f"Could not request results from speech recognition service; {e}")
        return f"Could not request results from speech recognition service; {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return f"Error processing the audio: {str(e)}"
