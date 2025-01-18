"""
Captures audio in real-time using PyAudio's callback mode and sends chunks
to the AudioProcessor for storage/saving.
"""

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
        PyAudio calls this whenever new audio data is available.
        We drop the data into our queue for the background processing thread.
        """
        self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start_stream(self):
        """
        Opens the stream in callback mode and starts a background thread to process data.
        """
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK,
                                  stream_callback=self.audio_callback)

        self.stream.start_stream()
        # Background thread reads from the queue and processes the data
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
        print("[AudioInterface] Stream started.")

    def _process_loop(self):
        """
        Continuously read audio chunks from the queue and pass them
        to the AudioProcessor until stop_flag is set.
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
        Also tells the AudioProcessor to save the audio to a file.
        """
        print("[AudioInterface] Stopping stream...")
        self.stop_flag = True

        if self.processing_thread is not None:
            self.processing_thread.join()

        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

        # Once everything is done, save the collected audio
        self.processor.save_audio_to_wav("saved_audio")

        print("[AudioInterface] Stream stopped and audio saved.")