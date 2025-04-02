# Audio Transcription Tool

A simple audio recording and transcription tool using OpenAI's Whisper model.

## Features

- Records audio in 5-minute segments
- Transcribes audio using Whisper's "medium" model
- Saves audio files and transcriptions with date and time information
- Logs recording duration every 5 minutes

## Directory Structure

- `saved_audio/` - Directory for storing recorded audio files
- `transcriptions/` - Directory for storing transcribed text files

## Installation

1. Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install PyAudio Prerequisites:

PyAudio often requires additional system libraries to be installed first:

**macOS:**
```bash
brew install portaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Windows:**
For Windows, PyAudio wheels are available and usually install without additional steps.

3. Install PyAudio:

```bash
pip install PyAudio
```

4. Install the remaining dependencies:

```bash
pip install -r requirements.txt
```

### Troubleshooting PyAudio Installation

If you encounter issues installing PyAudio:

**macOS:**
- Try installing the pre-compiled wheel: `pip install --no-cache-dir PyAudio`
- If that fails, try: `CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install PyAudio`

**Python 3.12+ Users:**
If you're using Python 3.12 and encounter `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`:
- Try using Python 3.11 or earlier
- Or install PyAudio from a wheel: `pip install --no-cache-dir PyAudio`

## Usage

Run the script with:

```bash
python main.py
```

To stop recording, press `Ctrl+C`.

## Output

- Audio files are saved in the `saved_audio/` directory with filenames like `Monday_2023-09-25_14-30-00.wav`
- Transcriptions are saved in the `transcriptions/` directory with matching filenames

## Requirements

- Python 3.7+ (Python 3.11 or earlier recommended for better compatibility)
- OpenAI Whisper
- PyAudio
- NumPy 