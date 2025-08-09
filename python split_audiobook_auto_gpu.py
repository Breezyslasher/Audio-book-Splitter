import re
import subprocess
import whisper
import torch
from pathlib import Path

# --- SETTINGS ---
INPUT_DIR = "."                # Folder with your audiobook files (mp3)
OUTPUT_DIR = "chapters"        # Folder to save chapters
MODEL_SIZE = "base"            # tiny, base, small, medium, large

# Regex to detect chapter names
pattern = re.compile(r"\b(chapter|part|prologue|epilogue)\s+(\d+|\w+)\b", re.IGNORECASE)

# Create output folder if not exists
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Detect device (GPU or CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Running Whisper on device: {device}")

# Load model on correct device
model = whisper.load_model(MODEL_SIZE).to(device)

# Global chapter count (continuous numbering)
chapter_counter = 1

# Sort all mp3 files alphabetically
audio_files = sorted(Path(INPUT_DIR).glob("*.mp3"))

for audio_file in audio_files:
    print(f"\nProcessing {audio_file} ...")
    # Transcribe with timestamps
    result = model.transcribe(str(audio_file))

    # Find chapter start times
    chapter_times = []
    for segment in result['segments']:
        text = segment['text'].strip()
        match = pattern.search(text)
        if match:
            start_time = segment['start']
            chapter_times.append((chapter_counter, start_time))
            chapter_counter += 1

    # If no chapters detected, save whole file as one chapter
    if not chapter_times:
        output_file = Path(OUTPUT_DIR) / f"Chapter_{chapter_counter:02}.mp3"
        print(f"No chapters detected, saving entire file as {output_file}")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(audio_file), "-c", "copy", str(output_file)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        chapter_counter += 1
        continue

    # Add end times for each chapter
    dur = result["segments"][-1]["end"]
    chapters_with_end = []
    for i, (num, start) in enumerate(chapter_times):
        end = chapter_times[i + 1][1] if i + 1 < len(chapter_times) else dur
        chapters_with_end.append((num, start, end))

    # Split audio by chapters using ffmpeg
    for num, start, end in chapters_with_end:
        output_file = Path(OUTPUT_DIR) / f"Chapter_{num:02}.mp3"
        print(f"Saving Chapter {num} from {start:.2f}s to {end:.2f}s as {output_file}")
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", str(audio_file),
            "-ss", str(start),
            "-to", str(end),
            "-c", "copy",
            str(output_file)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print(f"\n✅ Done! Chapters saved in '{OUTPUT_DIR}' folder.")
