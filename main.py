import datetime
import time
import sys
import os
import pyaudio
import wave
import whisper
import queue
import threading
import io

# ------------------------------------------------------------------------
# 1. FUNCTION TO CAPTURE TERMINAL OUTPUT AND SAVE TO A FILE
# ------------------------------------------------------------------------
def capture_terminal_output(input_text):
    """
    Captures any print statements made while sys.stdout is redirected,
    and saves them to 'terminal_output.txt'.
    """
    original_stdout = sys.stdout

    try:
        # Create an in-memory stream to capture prints
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # -------------------------------------------------------
        # Any print statements in this block go to captured_output
        print(input_text)
        # -------------------------------------------------------

    finally:
        # Restore the original stdout so we can print to console again
        sys.stdout = original_stdout

    # Now we can get the entire "terminal" output as a string
    everything_printed = captured_output.getvalue()

    # Save that to a file
    with open("terminal_output.txt", "a", encoding="utf-8") as f:
        f.write(everything_printed)


# ------------------------------------------------------------------------
# 2. AUDIO RECORDING CONFIG
# ------------------------------------------------------------------------
CHUNK = 1024              # Number of audio samples per chunk
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 1              # 1=Mono, 2=Stereo
RATE = 16000              # Sample rate (16k for speech)

# ------------------------------------------------------------------------
# 3. AUDIO PROCESSOR
# ------------------------------------------------------------------------
class AudioProcessor:
    def __init__(self):
        # Load Whisper model (change "medium" to any size you prefer)
        self.model = whisper.load_model("medium", device="cpu")
        
        # final_buffer holds ALL audio data from start to finish
        self.final_buffer = b""

        # partial_buffer is for partial, real-time transcriptions only
        self.partial_buffer = b""

        # We'll keep track of all recognized words here (for partial + final)
        self.transcript_words = []

        # This is how many bytes we need before we do a partial transcription.
        # 5 seconds * 16000 samples/second * 2 bytes/sample = 160,000 bytes
        self.partial_buffer_bytes = 5 * 16000 * 2

        print("[AudioProcessor] Initialized with Whisper model.")

    def process_chunk(self, audio_data: bytes):
        """
        Called for each chunk of audio data coming in.
        We'll accumulate the data in memory.
        - final_buffer stores everything until we stop.
        - partial_buffer accumulates data until it hits partial_buffer_bytes.
        """
        # Keep the entire chunk for final WAV
        self.final_buffer += audio_data

        # Also accumulate for partial transcription
        self.partial_buffer += audio_data

        if len(self.partial_buffer) >= self.partial_buffer_bytes:
            self._transcribe_and_reset_partial_buffer()

    def _transcribe_and_reset_partial_buffer(self):
        """
        Save the current partial buffer to a temporary WAV file,
        call Whisper to transcribe it, print out the partial transcript,
        then reset the partial buffer.
        """
        print("[AudioProcessor] Transcribing partial audio...")
        temp_filename = "temp_partial.wav"
        self._save_buffer_to_wav(temp_filename, self.partial_buffer)

        # Transcribe (could set task="translate" if you want English translation)
        result = self.model.transcribe(temp_filename)
        text = result["text"]
        capture_terminal_output(text)
        print(f"[Partial Translation]: {text}")

        # 1) Split text into words and store them
        words = text.split()
        self.transcript_words.extend(words)

        # 2) Clear the partial buffer
        self.partial_buffer = b""

        # 3) Cleanup temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    def _save_buffer_to_wav(self, filename, raw_data):
        """
        Saves the raw audio data to a WAV file so Whisper can read it.
        """
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(RATE)
            wf.writeframes(raw_data)

    def save_audio_to_wav(self, name):
        """
        When recording stops, save any remaining audio to a final file,
        and do a final transcription.
        """
        final_filename = f"{name}.wav"
        print(f"[AudioProcessor] Saving final audio to {final_filename}")

        # Save all recorded audio (the entire session)
        self._save_buffer_to_wav(final_filename, self.final_buffer)

        # Final transcription after recording is done
        result = self.model.transcribe(final_filename)
        text = result["text"]
        print(f"[Final Translation]: {text}")

        # Optionally store or split final words
        words = text.split()
        self.transcript_words.extend(words)

        # --------------------------------------------------------------------
        # ------------- Remove or Comment Out Unwanted Text File -------------
        # --------------------------------------------------------------------
        # This was the code that created final_recording_words.txt or similar.
        # Since you do NOT want that file, we comment it out.

        # os.makedirs(os.path.dirname(name), exist_ok=True)  # Ensure directory exists
        # transcript_txt_path = f"{name}_words.txt"
        # with open(transcript_txt_path, 'w', encoding='utf-8') as f:
        #     for w in self.transcript_words:
        #         f.write(w + "\n")
        # print(f"[AudioProcessor] Saved list of words to {transcript_txt_path}")
        # --------------------------------------------------------------------

        # Clear buffers after final use (optional)
        self.final_buffer = b""
        self.partial_buffer = b""
        # self.transcript_words.clear()

# ------------------------------------------------------------------------
# 4. AUDIO INTERFACE
# ------------------------------------------------------------------------
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

        # Generate a timestamp (e.g. 20250124_153500)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Build a unique filename using that timestamp
        unique_filename = f"saved_audio/final_recording_{timestamp}"

        # Save final audio and do a final transcription
        self.processor.save_audio_to_wav(unique_filename)

        print(f"[AudioInterface] Stream stopped and audio saved as {unique_filename}.wav")

# ------------------------------------------------------------------------
# 5. MAIN SCRIPT
# ------------------------------------------------------------------------
def main():
    # You can optionally suppress warnings if you like:
    # sys.stderr = open(os.devnull, 'w')

    audio_interface = AudioInterface()
    audio_interface.start_stream()

    print("Recording audio... Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Main] Ctrl+C detected. Stopping recording...")
        audio_interface.stop_stream()


if __name__ == "__main__":
    main()