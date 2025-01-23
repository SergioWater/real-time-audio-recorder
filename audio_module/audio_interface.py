import pyaudio
import queue
import threading
import time

from .config import CHUNK, FORMAT, CHANNELS, RATE
from .audio_processor import AudioProcessor

class AudioInterface:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.processor = AudioProcessor()
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.stop_flag = False
        self.processing_thread = None

    def audio_callback(self, in_data, frame_count, time_info, status_flags):
        """
        PyAudio calls this function whenever new audio data is available.
        We put that data into the queue so our background thread can process it.
        """
        self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start_stream(self):
        """
        Opens the audio stream in callback mode and starts a background thread.
        """
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self.audio_callback
        )

        self.stream.start_stream()

        # Background thread to fetch chunks from the queue and process them.
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
        print("[AudioInterface] Stream started.")

    def _process_loop(self):
        """
        Continuously read audio chunks from the queue and pass them to the AudioProcessor
        until stop_flag is set.
        """
        while not self.stop_flag:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                self.processor.process_chunk(audio_data)
            except queue.Empty:
                pass

    def stop_stream(self):
        """
        Stop recording, join the thread, and close resources.
        Save the final audio to a file and do a final transcription.
        """
        print("[AudioInterface] Stopping stream...")
        self.stop_flag = True

        if self.processing_thread is not None:
            self.processing_thread.join()

        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

        # Save final audio and do a final transcription
        self.processor.save_audio_to_wav("saved_audio")

        print("[AudioInterface] Stream stopped and audio saved.")