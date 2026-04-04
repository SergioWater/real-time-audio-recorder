import os
import time
import datetime
import threading
import sys
import calendar
import queue

from summarize import gemini_summarize

# Create main directories
os.makedirs("saved_audio", exist_ok=True)
os.makedirs("transcriptions", exist_ok=True)

# Create month directories for the rest of the year
def create_month_directories():
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    next_year = current_year + 1
    
    # Create directories for all months in the current year
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        month_dir_audio = os.path.join("saved_audio", f"{current_year}_{month_name}")
        month_dir_transcription = os.path.join("transcriptions", f"{current_year}_{month_name}")
        os.makedirs(month_dir_audio, exist_ok=True)
        os.makedirs(month_dir_transcription, exist_ok=True)
    
    # Create directories for all months in the next year
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        month_dir_audio = os.path.join("saved_audio", f"{next_year}_{month_name}")
        month_dir_transcription = os.path.join("transcriptions", f"{next_year}_{month_name}")
        os.makedirs(month_dir_audio, exist_ok=True)
        os.makedirs(month_dir_transcription, exist_ok=True)
    
    print(f"Created month directories for {current_year} and {next_year}")

# Create month directories
create_month_directories()

# Check for required dependencies with helpful error messages
try:
    import numpy as np
    print("NumPy loaded successfully")
except ImportError:
    print("Error: NumPy is not installed. Please run: pip install numpy")
    sys.exit(1)

try:
    import pyaudio
    print("PyAudio loaded successfully")
except ImportError:
    print("Error: PyAudio is not installed.")
    print("\nOn macOS, install portaudio first:")
    print("    brew install portaudio")
    print("Then install PyAudio:")
    print("    pip install PyAudio")
    print("\nOn Ubuntu/Debian:")
    print("    sudo apt-get install portaudio19-dev")
    print("    pip install PyAudio")
    print("\nOn Windows, try:")
    print("    pip install PyAudio")
    sys.exit(1)

try:
    import wave
    print("Wave module loaded successfully")
except ImportError:
    print("Error: wave module not found. This should be part of the standard library.")
    sys.exit(1)

try:
    import whisper
    print("Whisper loaded successfully")
except ImportError:
    print("Error: OpenAI Whisper is not installed. Please run: pip install openai-whisper")
    sys.exit(1)

from pathlib import Path

# Initialize Whisper model with medium size for balanced CPU usage
try:
    print("Loading Whisper model (this may take a moment)...")
    model = whisper.load_model("medium")
    print("Whisper model loaded successfully")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    print("Please make sure you have enough disk space and a proper internet connection.")
    sys.exit(1)

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 1800  # 30 minutes (1800 seconds)
CHUNK_DURATION = 15    # Process transcription in 15-second chunks

# Function to verify if a file was created and contains data
def verify_file_created(filepath, min_size_bytes=100):
    if not os.path.exists(filepath):
        print(f"ERROR: File {filepath} was not created!")
        return False
        
    file_size = os.path.getsize(filepath)
    if file_size < min_size_bytes:
        print(f"WARNING: File {filepath} is suspiciously small ({file_size} bytes)!")
        return False
        
    print(f"SUCCESS: File {filepath} was created successfully ({file_size} bytes)")
    return True

# Function to list all available audio input devices
def list_audio_devices():
    p = pyaudio.PyAudio()
    info = f"\nAvailable audio input devices:\n"
    info += f"{'-' * 50}\n"
    
    try:
        # Get the default input device
        default_device = p.get_default_input_device_info()
        info += f"Default device: {default_device['name']} (index: {default_device['index']})\n\n"
    except Exception as e:
        info += f"Error getting default device: {e}\n\n"
    
    for i in range(p.get_device_count()):
        try:
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # if the device has input channels
                info += f"Device {i}: {device_info['name']}\n"
                info += f"  Input channels: {device_info['maxInputChannels']}\n"
                info += f"  Sample rate: {int(device_info['defaultSampleRate'])}\n"
        except Exception as e:
            info += f"Device {i}: Error getting device info - {e}\n"
    
    p.terminate()
    return info

# Function to format time in HH:MM:SS
def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

# Function to save a WAV file from frames
def save_wav_file(filename, frames, audio_format, channels, rate):
    try:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(audio_format)
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
        
        if verify_file_created(filename, min_size_bytes=1000):
            print(f"Audio saved to {filename}")
            return True
        else:
            print(f"Failed to save valid audio file {filename}")
            return False
    except Exception as e:
        print(f"Error saving audio file: {e}")
        return False

# Function to record audio and transcribe in real-time
def record_and_transcribe(audio_filename, transcript_filename, input_device=None):
    try:
        audio = pyaudio.PyAudio()
        
        # Print available devices for debugging
        print(list_audio_devices())
        
        # Open stream with specific device if provided
        stream_params = {
            'format': FORMAT,
            'channels': CHANNELS,
            'rate': RATE,
            'input': True,
            'frames_per_buffer': CHUNK
        }
        
        if input_device is not None:
            stream_params['input_device_index'] = input_device
            
        try:
            stream = audio.open(**stream_params)
            print("Audio stream opened successfully!")
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            print("\nTry specifying a different input device from the list above.")
            audio.terminate()
            return False
        
        print(f"Starting recording session for {format_time(RECORD_SECONDS)} (HH:MM:SS)")
        all_frames = []  # Store all audio frames for the complete recording
        chunk_frames = []  # Store frames for the current chunk
        
        # Calculate parameters
        total_chunks = int(RATE / CHUNK * RECORD_SECONDS)
        chunks_per_segment = int(RATE / CHUNK * CHUNK_DURATION)
        
        # Create a queue to store audio chunks for transcription
        audio_queue = queue.Queue()
        
        # Flag to signal the transcription thread to stop
        stop_transcription = threading.Event()
        
        # Variable to store all transcription text (shared between threads)
        all_transcription = []
        
        # Lock for thread-safe operations on the transcription
        transcription_lock = threading.Lock()
        
        # Function to transcribe audio chunks in a separate thread
        def transcribe_chunks():
            chunk_count = 0
            
            # Open transcript file and keep it open for appending
            with open(transcript_filename, 'w') as transcript_file:
                while not stop_transcription.is_set() or not audio_queue.empty():
                    try:
                        if not audio_queue.empty():
                            # Get the next chunk of audio frames from the queue
                            chunk_data = audio_queue.get()
                            chunk_count += 1
                            
                            # Save to a temporary file for transcription
                            temp_filename = f"temp_chunk_{chunk_count}.wav"
                            with wave.open(temp_filename, 'wb') as wf:
                                wf.setnchannels(CHANNELS)
                                wf.setsampwidth(audio.get_sample_size(FORMAT))
                                wf.setframerate(RATE)
                                wf.writeframes(b''.join(chunk_data))
                            
                            # Transcribe the chunk
                            try:
                                print(f"\nTranscribing chunk {chunk_count}...")
                                result = model.transcribe(temp_filename)
                                chunk_text = result["text"].strip()
                                
                                # Append to the complete transcription
                                with transcription_lock:
                                    all_transcription.append(chunk_text)
                                    
                                    # Write to the transcript file
                                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                                    transcript_file.write(f"[Chunk {chunk_count} - {timestamp}] {chunk_text}\n\n")
                                    transcript_file.flush()  # Ensure it's written to disk
                                
                                # Display the transcription
                                print(f"\n--- LIVE TRANSCRIPTION (CHUNK {chunk_count}) ---")
                                print(chunk_text)
                                print("----------------------------------------\n")
                            except Exception as e:
                                print(f"Error transcribing chunk {chunk_count}: {e}")
                            
                            # Clean up the temporary file
                            try:
                                os.remove(temp_filename)
                            except:
                                pass
                            
                            # Mark the task as done
                            audio_queue.task_done()
                        else:
                            # No chunks to process, wait a bit
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"Error in transcription thread: {e}")
                        time.sleep(1)  # Wait a bit before retrying
        
        # Start the transcription thread
        transcription_thread = threading.Thread(target=transcribe_chunks, daemon=True)
        transcription_thread.start()
        
        # Function to display progress
        def show_progress():
            start_time = time.time()
            
            while not stop_transcription.is_set():
                elapsed = time.time() - start_time
                remaining = max(0, RECORD_SECONDS - elapsed)
                progress = min(100, (elapsed / RECORD_SECONDS) * 100)
                
                # Create a progress bar
                bar_length = 30
                filled_length = int(bar_length * progress / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # Get current time
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                
                # Count transcribed chunks
                with transcription_lock:
                    chunk_count = len(all_transcription)
                
                print(f"\rRecording: {progress:.1f}% [{bar}] Elapsed: {format_time(elapsed)} Remaining: {format_time(remaining)} | Chunks transcribed: {chunk_count} | Time: {current_time}", end="", flush=True)
                time.sleep(1)  # Update every second
            
            print()  # New line after recording is done
        
        # Start the progress display thread
        progress_thread = threading.Thread(target=show_progress, daemon=True)
        progress_thread.start()
        
        try:
            # Main recording loop
            for i in range(total_chunks):
                # Read audio data
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # Add to both the complete recording and the current chunk
                all_frames.append(data)
                chunk_frames.append(data)
                
                # If we've collected a full chunk, send it for transcription
                if len(chunk_frames) >= chunks_per_segment:
                    # Add this chunk to the queue for transcription
                    audio_queue.put(chunk_frames.copy())
                    
                    # Clear the chunk frames for the next segment
                    chunk_frames = []
                    
            # Don't forget the last partial chunk if there is one
            if chunk_frames:
                audio_queue.put(chunk_frames)
                
        except KeyboardInterrupt:
            print("\nRecording stopped by user.")
        except Exception as e:
            print(f"\nError during recording: {e}")
        finally:
            # Signal the transcription thread to finish
            stop_transcription.set()
            
            # Wait for the transcription queue to be emptied
            audio_queue.join()
            
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save the complete audio recording
            success = save_wav_file(
                audio_filename, 
                all_frames, 
                audio.get_sample_size(FORMAT), 
                CHANNELS, 
                RATE
            )
            
            # Wait for transcription to finish
            transcription_thread.join(timeout=30)
            
            # Final transcription summary
            with transcription_lock:
                total_chunks = len(all_transcription)
                
            print(f"\nRecording and live transcription complete!")
            print(f"Total audio chunks transcribed: {total_chunks}")
            
            return success
    except Exception as e:
        print(f"Error in record_and_transcribe: {e}")
        return False

# Main function
def main():
    # Ask for input device selection
    try:
        print(list_audio_devices())
        device_input = input("Enter input device index (leave blank for default): ").strip()
        input_device = int(device_input) if device_input else None
        print(f"Using input device: {input_device if input_device is not None else 'Default'}")
    except ValueError:
        print("Invalid input. Using default device.")
        input_device = None
    
    try:
        # Generate filenames with current day and date
        current_datetime = datetime.datetime.now()
        day_name = current_datetime.strftime("%A")
        date_str = current_datetime.strftime("%Y-%m-%d")
        timestamp = current_datetime.strftime("%H-%M-%S")
        month_name = calendar.month_name[current_datetime.month]
        year = current_datetime.year
        
        # Use month-based directory structure
        month_dir_audio = os.path.join("saved_audio", f"{year}_{month_name}")
        month_dir_transcription = os.path.join("transcriptions", f"{year}_{month_name}")
        
        audio_filename = os.path.join(month_dir_audio, f"{day_name}_{date_str}_{timestamp}.wav")
        transcript_filename = os.path.join(month_dir_transcription, f"{day_name}_{date_str}_{timestamp}.txt")
        
        print(f"Starting recording session. Audio will be saved to: {audio_filename}")
        print(f"Live transcription will be saved to: {transcript_filename}")
        
        # Record audio and transcribe in real-time
        success = record_and_transcribe(audio_filename, transcript_filename, input_device)
        
        if success:
            print(f"Session completed successfully. Transcription saved to {transcript_filename}")
            # Auto-summarise the completed transcript
            try:
                print("\nAuto-summarising transcript with Gemini...")
                gemini_summarize(transcript_filename)
            except Exception as e:
                print(f"Warning: Auto-summarisation failed: {e}")
        else:
            print("Session completed with errors.")
            
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    print("\nProgram completed. Run again for another recording session.")

if __name__ == "__main__":
    main() 