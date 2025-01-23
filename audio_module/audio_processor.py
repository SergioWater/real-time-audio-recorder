import wave
import os
import whisper

class AudioProcessor:
    def __init__(self):
        # Load Whisper model. Possible options: "tiny", "base", "small", "medium", "large", etc.
        # Using "small" here for a balance of speed and accuracy.
        self.model = whisper.load_model("small", device="cpu")
        
        # We'll store raw audio data here as bytes
        self.audio_buffer = b""

        # Decide how big each chunk of audio should be before we do a "partial" transcription.
        # For example: 5 seconds * 16000 samples/sec * 2 bytes/sample = 160000 bytes
        self.partial_buffer_bytes = 5 * 16000 * 2

        print("[AudioProcessor] Initialized with Whisper model.")

    def process_chunk(self, audio_data: bytes):
        """
        This method is called for each chunk of audio data coming in.
        We'll accumulate the data in memory and decide when to transcribe.
        """
        self.audio_buffer += audio_data

        # If our buffer exceeds the threshold (e.g., 5 seconds of audio),
        # do a partial transcription and reset the buffer.
        if len(self.audio_buffer) >= self.partial_buffer_bytes:
            self._transcribe_and_reset_buffer()

    def _transcribe_and_reset_buffer(self):
        """
        Save the current buffer to a temporary WAV file, call Whisper to transcribe,
        print out the partial transcript, then reset the buffer.
        """
        print("[AudioProcessor] Transcribing partial audio...")

        temp_filename = "temp_partial.wav"
        self._save_buffer_to_wav(temp_filename, self.audio_buffer)

        # If you want to force English translation from any language, use task="translate"
        # e.g. result = self.model.transcribe(temp_filename, task="translate")
        result = self.model.transcribe(temp_filename)

        print(f"[Partial Translation]: {result['text']}")

        # Clear the buffer
        self.audio_buffer = b""

        # Cleanup temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    def _save_buffer_to_wav(self, filename, raw_data):
        """
        Saves the raw audio data to a WAV file so Whisper can read it.
        """
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)         # Mono
        wf.setsampwidth(2)         # 16-bit
        wf.setframerate(16000)     # 16k sample rate
        wf.writeframes(raw_data)
        wf.close()

    def save_audio_to_wav(self, name):
        """
        When recording stops, save any remaining audio to a final file and do a final transcription.
        """
        final_filename = f"{name}.wav"
        print(f"[AudioProcessor] Saving final audio to {final_filename}")
        self._save_buffer_to_wav(final_filename, self.audio_buffer)

        # Final transcription after recording is done
        result = self.model.transcribe(final_filename)
        print(f"[Final Translation]: {result['text']}")

        # Clear buffer after final use
        self.audio_buffer = b""