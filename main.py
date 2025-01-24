import time
import sys
import os
from audio_module.audio_interface import AudioInterface
sys.stderr = open(os.devnull, 'w')
def main():
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