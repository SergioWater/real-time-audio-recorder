import pyaudio

# Audio recording config
CHUNK = 1024              # Number of audio samples per chunk
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 1              # 1=Mono, 2=Stereo
RATE = 16000              # Sample rate (16k for speech)