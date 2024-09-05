import wave
import struct

# Audio parameters
duration = 1  # seconds
sample_rate = 16000
num_channels = 1
sample_width = 2

# Create silent audio data
num_frames = duration * sample_rate
audio_data = struct.pack(f'{num_frames}h', *([0] * num_frames))

# Write to WAV file
with wave.open('test_audio.wav', 'wb') as wav_file:
    wav_file.setnchannels(num_channels)
    wav_file.setsampwidth(sample_width)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(audio_data)

print("Test audio file 'test_audio.wav' created successfully.")