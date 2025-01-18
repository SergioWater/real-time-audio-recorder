"""
Entry point. Creates an AudioInterface, starts the stream, and
stops recording when the user presses Ctrl+C.
"""

from audio_module.audio_interface import AudioInterface
import time

def main():
    audio_interface = AudioInterface()
    audio_interface.start_stream()

    print("Recording audio... Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("[Main] Ctrl+C detected. Stopping recording...")
        audio_interface.stop_stream()

if __name__ == "__main__":
    main()