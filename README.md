Live Translation App with PyAudio & Whisper

This repository contains a simple real-time transcription (and optional translation) application using PyAudio for capturing audio in real-time and OpenAI Whisper for transcription. It is set up to chunk audio every few seconds and produce partial transcripts until you press Ctrl+C, at which point it will finalize the output.

Table of Contents
	1.	Features
	2.	Project Structure
	3.	Installation
	•	Create a Conda Environment
	•	Install Dependencies
	•	PyAudio on Apple Silicon (M1/M2)
	4.	Usage
	5.	Troubleshooting
	6.	License

  Features
	•	Live Audio Capture: Uses PyAudio to capture audio in real time.
	•	Partial Transcriptions: Every few seconds, a chunk of audio is sent to Whisper for transcription.
	•	Final Transcription: After you press Ctrl+C, a final transcription runs on the entire audio buffer.
	•	Model Customization: You can switch Whisper models (e.g., tiny, base, small, medium, large) for speed or accuracy.
	•	Translation vs. Transcription: Configure Whisper’s task="translate" if you want to force translation into English from another language.

  live_translation_app/
├── main.py

 	•	main.py: Entry point that starts/stops the audio capture.
	•	requirements.txt: Lists core Python packages.
	•	audio_module/: Contains modules for audio recording and processing.
	•	config.py: Audio configuration (sample rate, chunk size, etc.).
	•	audio_interface.py: Manages PyAudio’s stream, captures data in callback mode, and launches a background thread to process audio.
	•	audio_processor.py: Accumulates raw audio, periodically transcribes with Whisper, and saves final audio.
	•	my_ai_model.py: Placeholder for additional AI features (if needed).

  Installation

1. Create a Conda Environment

conda create -n voice_2 python=3.10
conda activate voice_2

2. Install Dependencies

Make sure to install the packages listed in requirements.txt. Typically:
pip install -r requirements.txt

You may also need ffmpeg at the system or conda level for Whisper to handle audio:
conda install ffmpeg