# Audio Transcription and Summarization Tool

A comprehensive audio recording, transcription, and summarization tool using OpenAI's Whisper model and BART for summarization.

## Features

- Records audio in 30-minute segments
- Provides real-time transcription during recording
- Transcribes audio using Whisper's "medium" model
- Creates abstractive summaries of transcriptions
- Organizes files by year, month, and day
- Displays progress with a visual interface

## Directory Structure

- `saved_audio/YEAR_MONTH/` - Directories for storing recorded audio files
- `transcriptions/YEAR_MONTH/` - Directories for storing transcribed text files
- `summaries/YEAR/MONTH/DAY/` - Directories for storing abstractive summaries

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

3. Install all required dependencies:

```bash
pip install PyAudio numpy openai-whisper transformers torch
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

### Recording and Transcription

Run the main script for audio recording and live transcription:

```bash
python main.py
```

This will:
1. Record 30 minutes of audio
2. Provide live transcription during recording
3. Save both the audio file and transcript in month-based folders
4. Show a progress bar with continuous updates

To stop recording early, press `Ctrl+C`.

### Summarization

To generate abstractive summaries of your transcriptions, run:

```bash
# Summarize all transcription files
python summarize.py

# Summarize a specific transcription file
python summarize.py transcriptions/2024_April/Monday_2024-04-02_14-30-00.txt
```

The summarization script will:
1. Process transcript files (either all or one specific file)
2. Create year/month/day-based directories
3. Generate abstractive summaries using BART
4. Save summaries in the organized directory structure
5. Show a preview of each summary

## Output Files

- **Audio files**: `saved_audio/2024_April/Monday_2024-04-02_14-30-00.wav`
- **Transcriptions**: `transcriptions/2024_April/Monday_2024-04-02_14-30-00.txt`
- **Summaries**: `summaries/2024/April/02/Monday_2024-04-02_14-30-00_summary.txt`

## Requirements

- Python 3.7+ (Python 3.11 or earlier recommended for better compatibility)
- OpenAI Whisper (for transcription)
- PyAudio (for recording)
- NumPy (for audio processing)
- Transformers (for summarization)
- PyTorch (for summarization model) 