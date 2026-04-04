from google import genai
import os
import sys
import re
import datetime
import calendar
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GEMINI_MODEL = "gemini-1.5-flash"
SUMMARY_PROMPT = (
    "Summarize the following lecture/lesson transcript into concise notes "
    "with key points and takeaways:\n\n"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_summary_directory(year, month, day):
    """
    Create directory structure for summaries based on date.
    Returns the path to the directory.
    """
    month_name = calendar.month_name[month]
    summary_dir = os.path.join("summaries", f"{year}", f"{month_name}", f"{day:02d}")
    os.makedirs(summary_dir, exist_ok=True)
    return summary_dir


def extract_date_from_filename(filename):
    """
    Extract date information from the transcript filename.
    Expected format: something_YYYY-MM-DD_HH-MM-SS.txt
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2})_', os.path.basename(filename))
    if match:
        year, month, day = map(int, match.group(1).split('-'))
        return year, month, day

    now = datetime.datetime.now()
    return now.year, now.month, now.day


# ---------------------------------------------------------------------------
# Gemini summarisation
# ---------------------------------------------------------------------------

def gemini_summarize(transcript_file):
    """
    Read a transcript file, send it to the Gemini API for summarisation,
    and save the result to the summaries directory.

    Returns (summary_text, output_path) on success, or (None, None) on failure.
    """
    # --- Read the transcript ------------------------------------------------
    try:
        with open(transcript_file, 'r') as f:
            full_text = f.read()
    except FileNotFoundError:
        print(f"Error: File {transcript_file} not found.")
        return None, None

    if not full_text.strip():
        print(f"Warning: Transcript file {transcript_file} is empty. Skipping.")
        return None, None

    # Strip timestamp headers (e.g. "[Chunk 3 - 12:34:56]")
    clean_text = re.sub(r'\[Chunk \d+ - \d+:\d+:\d+\]\s*', '', full_text)

    # --- Call Gemini API ----------------------------------------------------
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set. Skipping summarisation.")
        return None, None

    try:
        client = genai.Client(api_key=api_key)

        print(f"Sending transcript to Gemini ({GEMINI_MODEL}) for summarisation...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=SUMMARY_PROMPT + clean_text,
        )
        summary_text = response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None, None

    # --- Save the summary ---------------------------------------------------
    year, month, day = extract_date_from_filename(transcript_file)
    summary_dir = create_summary_directory(year, month, day)

    original_name = os.path.splitext(os.path.basename(transcript_file))[0]
    output_file = os.path.join(summary_dir, f"{original_name}_summary.txt")

    try:
        with open(output_file, 'w') as f:
            f.write(summary_text)
    except Exception as e:
        print(f"Error saving summary file: {e}")
        return None, None

    print(f"Summary saved to: {output_file}")
    print("\nSummary Preview:")
    print("-" * 40)
    preview = summary_text[:300] + ("..." if len(summary_text) > 300 else "")
    print(preview)
    print("-" * 40)

    return summary_text, output_file


# ---------------------------------------------------------------------------
# Batch mode
# ---------------------------------------------------------------------------

def summarize_all_transcripts(transcriptions_dir="transcriptions"):
    """
    Find and summarise all transcript files in the transcriptions directory.
    """
    transcript_files = []
    for root, _, files in os.walk(transcriptions_dir):
        for file in files:
            if file.endswith(".txt") and not file.endswith("_summary.txt"):
                transcript_files.append(os.path.join(root, file))

    if not transcript_files:
        print(f"No transcript files found in {transcriptions_dir}")
        return

    print(f"Found {len(transcript_files)} transcript files")
    print("-" * 40)

    for i, tf in enumerate(transcript_files):
        print(f"Processing file {i+1}/{len(transcript_files)}: {tf}")
        gemini_summarize(tf)
        print("-" * 40)

    print("All transcripts have been summarised!")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("No specific transcript provided. Summarising all transcripts...")
        summarize_all_transcripts()
    elif len(sys.argv) == 2:
        gemini_summarize(sys.argv[1])
    else:
        print("Usage:")
        print("  python summarize.py                  # Summarise all transcripts")
        print("  python summarize.py <transcript_file> # Summarise specific transcript")
        sys.exit(1)
