
import re
import subprocess
import whisper
import torch
from pathlib import Path
from tqdm import tqdm

# --- SETTINGS ---
INPUT_DIR = "."                # Folder with your audiobook files (mp3)
OUTPUT_DIR = "chapters"        # Folder to save chapters
MODEL_SIZE = "base"            # tiny, base, small, medium, large
LOG_FILE = Path(OUTPUT_DIR) / "chapters_detected.txt"


input_files = sorted(Path(INPUT_DIR).glob("*.mp3"))
if not input_files:
    print("No MP3 files found to combine!")
    exit(1)

filelist_path = Path(INPUT_DIR) / "filelist.txt"
with filelist_path.open("w", encoding="utf-8") as f:
    for mp3_file in input_files:
        f.write(f"file '{mp3_file.as_posix()}'\n")

combined_path = Path(INPUT_DIR) / "audiobook.wav"

print("Combining all mp3 files into audiobook.wav...")
combine_cmd = [
    "ffmpeg", "-f", "concat", "-safe", "0", "-i",
    str(filelist_path), "-c:a", "pcm_s16le", "audiobook.wav"
]
result = subprocess.run(combine_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode != 0:
    print("Error combining files:", result.stderr.decode())
    exit(1)
print("Combine complete.\n")

# Regex to detect chapter names
pattern = re.compile(
    r"\b(?:chapter|part|prologue|epilogue)\s+("
    r"([1-9]|[1-4][0-9]|50)|"                        # digits 1-50
    r"(one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|twenty-one|twenty-two|twenty-three|twenty-four|twenty-five|"
    r"twenty-six|twenty-seven|twenty-eight|twenty-nine|thirty|"
    r"thirty-one|thirty-two|thirty-three|thirty-four|thirty-five|"
    r"thirty-six|thirty-seven|thirty-eight|thirty-nine|forty|"
    r"forty-one|forty-two|forty-three|forty-four|forty-five|"
    r"forty-six|forty-seven|forty-eight|forty-nine|fifty)"
    r")\b",
    re.IGNORECASE
)

# Create output folder if not exists
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Prepare log file
LOG_FILE.write_text("=== Chapter Detection Log ===\n\n")

# Detect device (GPU or CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Running Whisper on device: {device}")

# Load model on correct device
model = whisper.load_model(MODEL_SIZE).to(device)

# Global chapter count (continuous numbering)
chapter_counter = 1


# Now process only combined audiobook.mp3
audio_files = [combined_path]
for audio_file in audio_files:
    # Your processing code here
    print(f"Processing {audio_file}")

# Process each audiobook file with progress bar
for audio_file in tqdm(audio_files, desc="Audio files", unit="file"):
    # Transcribe with timestamps
    result = model.transcribe(str(audio_file))

    LOG_FILE.write_text  # Not needed here — just reminder: we append later

    # Find chapter start times
    chapter_times = []
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(f"--- {audio_file.name} ---\n")
        first_chapter = True
        for segment in result['segments']:
            text = segment['text'].strip()
            match = pattern.search(text)
            if match:
                # If this is the very first chapter in the whole book, start from 0.0
                if first_chapter:
                    start_time = 0.0
                    first_chapter = False
                else:
                    start_time = segment['start']
                chapter_times.append((chapter_counter, start_time))
                log.write(f"[{start_time:.2f}s] {text}\n")
                chapter_counter += 1
        log.write("\n")
    # If no chapters detected, save whole file as one chapter
    if not chapter_times:
        output_file = Path(OUTPUT_DIR) / f"Chapter_{chapter_counter:02}.wav"
        tqdm.write(f"No chapters detected in {audio_file.name}, saving entire file as {output_file.name}")
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

    # Split audio by chapters using ffmpeg with progress bar
    for num, start, end in tqdm(chapters_with_end, desc=f"Splitting {audio_file.name}", unit="chapter", leave=False):
        output_file = Path(OUTPUT_DIR) / f"Chapter_{num:02}.wav"
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
print(f"📄 Log of detected chapters saved in: {LOG_FILE}")
