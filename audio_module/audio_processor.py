"""
Handles the logic of what to do with each chunk of audio, and saves all
collected chunks into a single WAV file when recording ends.
"""

import wave
import pyaudio
from datetime import datetime
from .config import FORMAT, CHANNELS, RATE

class AudioProcessor:
    def __init__(self):
        # We'll collect audio chunks here until we're done
        self.frames = []

    def process_chunk(self, audio_data: bytes):
        """
        Called for every chunk of audio as it arrives.
        We add it to our frame list so we can save later.
        """
        self.frames.append(audio_data)

    def save_audio_to_wav(self, output_directory="saved_audio"):
        """
        Once recording is finished, we'll write all frames to a WAV file.
        We generate a unique filename using the current date/time.
        """
        # Unique file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_directory}/output_{timestamp}.wav"

        # Create a PyAudio instance to determine correct sample width
        pa = pyaudio.PyAudio()
        sample_width = pa.get_sample_size(FORMAT)
        pa.terminate()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(sample_width)
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.frames))

        print(f"[AudioProcessor] Saved audio to {filename}")