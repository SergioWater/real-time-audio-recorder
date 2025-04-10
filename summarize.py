from transformers import pipeline, T5Tokenizer, T5ForConditionalGeneration
import os
import sys
import re
import datetime
import calendar
import glob

def create_summary_directory(year, month, day):
    """
    Create directory structure for summaries based on date
    Returns the path to the directory
    """
    # Get month name
    month_name = calendar.month_name[month]
    
    # Create directory structure: summaries/YEAR/MONTH/DAY
    summary_dir = os.path.join("summaries", f"{year}", f"{month_name}", f"{day:02d}")
    os.makedirs(summary_dir, exist_ok=True)
    
    return summary_dir

def extract_date_from_filename(filename):
    """
    Extract date information from the transcript filename
    Expected format: something_YYYY-MM-DD_HH-MM-SS.txt
    """
    # Extract date pattern
    match = re.search(r'(\d{4}-\d{2}-\d{2})_', os.path.basename(filename))
    
    if match:
        date_str = match.group(1)
        # Parse the date
        year, month, day = map(int, date_str.split('-'))
        return year, month, day
    
    # If no date found in filename, use current date
    now = datetime.datetime.now()
    return now.year, now.month, now.day

def abstractive_summarize(transcript_file, output_dir=None):
    """
    Perform abstractive summarization on transcript file and save to organized directory.
    """
    print(f"Loading transcript from: {transcript_file}")
    
    # Read the transcript file
    try:
        with open(transcript_file, 'r') as f:
            full_text = f.read()
    except FileNotFoundError:
        print(f"Error: File {transcript_file} not found.")
        return
    
    # Remove timestamp headers
    clean_text = re.sub(r'\[Chunk \d+ - \d+:\d+:\d+\]\s*', '', full_text)
    
    print("Loading T5 model (this may take a moment)...")
    # Load T5 model and tokenizer
    model_name = "t5-base"  # Using T5 base model
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
    
    print("Performing summarization...")
    # Process in sections if text is long
    max_chunk_length = 1024  # Maximum length for each chunk to process
    min_chunk_length = 100   # Minimum length to consider summarization
    
    # Break text into manageable chunks
    sections = [clean_text[i:i+max_chunk_length] for i in range(0, len(clean_text), max_chunk_length)]
    
    summaries = []
    # Process every 10 chunks together
    for i in range(0, len(sections), 10):
        combined_chunks = " ".join(sections[i:i+10])
        if len(combined_chunks.strip()) > min_chunk_length:
            print(f"Summarizing chunks {i+1}-{min(i+10, len(sections))}/{len(sections)}...")
            # Parameters for the summary generation
            summary = summarizer(combined_chunks, 
                                max_length=150,  # Increased max length for combined chunks
                                min_length=50,   # Increased min length for combined chunks
                                do_sample=False  # Deterministic generation
                               )[0]["summary_text"]
            summaries.append(summary)
        else:
            # For very short sections, just include them as-is
            if combined_chunks.strip():
                summaries.append(combined_chunks.strip())
    
    # Combine all summaries
    final_summary = "\n\n".join(summaries)
    
    # Extract date from filename or use current date
    year, month, day = extract_date_from_filename(transcript_file)
    
    # Create directory for summary based on date
    summary_dir = create_summary_directory(year, month, day)
    
    # Generate output filename
    timestamp = datetime.datetime.now().strftime("%H-%M-%S")
    original_filename = os.path.splitext(os.path.basename(transcript_file))[0]
    output_file = os.path.join(summary_dir, f"{original_filename}_summary.txt")
    
    # Save the summary
    with open(output_file, 'w') as f:
        f.write(final_summary)
    
    print(f"Summary saved to: {output_file}")
    print("\nSummary Preview:")
    print("-" * 40)
    preview_length = min(300, len(final_summary))
    print(final_summary[:preview_length] + ("..." if len(final_summary) > preview_length else ""))
    print("-" * 40)
    
    return final_summary, output_file

def summarize_all_transcripts(transcriptions_dir="transcriptions"):
    """
    Find and summarize all transcript files in the transcriptions directory
    """
    # Get all text files recursively in transcriptions directory
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
    
    # Process each transcript file
    for i, transcript_file in enumerate(transcript_files):
        print(f"Processing file {i+1}/{len(transcript_files)}: {transcript_file}")
        abstractive_summarize(transcript_file)
        print("-" * 40)
    
    print("All transcripts have been summarized!")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) == 1:
        # No arguments, summarize all transcripts
        print("No specific transcript provided. Summarizing all transcripts...")
        summarize_all_transcripts()
    elif len(sys.argv) == 2:
        # Specific transcript file provided
        transcript_file = sys.argv[1]
        abstractive_summarize(transcript_file)
    else:
        print("Usage:")
        print("  python summarize.py                  # Summarize all transcripts")
        print("  python summarize.py <transcript_file> # Summarize specific transcript")
        sys.exit(1) 
