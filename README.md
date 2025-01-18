# Real-Time Audio Processing

This project is designed to capture audio from a microphone in real time and process it using a modular and highly optimized Python codebase. The captured audio is fed to a processing module, making it suitable for integration with AI models or other real-time applications.

This project continuously records audio in real time, sends each chunk to an AI model, **and** saves the entire recording as a WAV file in `saved_audio/` when you stop. Perfect if you want to capture data and also do on-the-fly processing or training with an AI module.


## Features

- **Real-Time Audio Capture**: Captures audio using PyAudio with minimal latency.
- **Modular Design**: The codebase is divided into clear modules:
  - `config.py` for audio settings.
  - `audio_interface.py` for managing the audio stream and callbacks.
  - `audio_processor.py` for processing audio data (e.g., sending to an AI model).
- **Thread-Safe Queue**: Ensures smooth handling of audio data between capture and processing.
- **Extensible**: Easily adapt the `AudioProcessor` class to include custom logic like AI inference or audio transformations.

---

## Project Structure

my_project/
├── README.md
├── requirements.txt
├── main.py
├── saved_audio/
└── audio_module/
├── init.py
├── config.py
├── audio_processor.py
└── audio_interface.py

## Getting Started

### Prerequisites

- Python 3.7 or later
- A microphone connected to your computer
- Required Python libraries:
  - `pyaudio` (for capturing audio)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd my_project

   pip install -r requirements.txt

   python main.py

###Configuration

All audio settings are stored in audio_module/config.py. You can adjust the following parameters:
	•	CHUNK: The number of audio samples per chunk (default: 1024).
	•	FORMAT: Audio sample format (default: pyaudio.paInt16).
	•	CHANNELS: Number of audio channels (1 for mono, 2 for stereo).
	•	RATE: Sampling rate in Hz (default: 16000).