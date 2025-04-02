#!/bin/bash

echo "Installing dependencies for Voice Recorder with Transcription..."

# Install portaudio (for macOS)
which brew > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Installing portaudio via Homebrew..."
    brew install portaudio
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install numpy
pip install openai-whisper
pip install PyAudio

echo "Dependencies installed. Now run your app with:"
echo "source .venv/bin/activate  # Activate virtual environment"
echo "python main.py             # Run the application" 