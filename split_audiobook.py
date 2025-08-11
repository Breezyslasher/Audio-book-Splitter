#!/usr/bin/env python3
import re
import subprocess
import platform
import whisper
import torch
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

class AudiobookSplitterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audiobook Chapter Splitter")
        self.geometry("800x600")

        # Variables
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.status_text = tk.StringVar(value="Select folders and start.")

        # UI Setup
        self.create_widgets()

        self.model = None
        self.chapter_counter = 1
        self.pattern = re.compile(
            r"\b(?:chapter|part|prologue|epilogue)\s+("
            r"([1-9]|[1-4][0-9]|50)|"
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
    def open_output_folder(self):
        path = self.output_dir.get()
        if not path:
            messagebox.showerror("Error", "Output folder path is not set.")
            return
        path = Path(path)
        if not path.exists():
            messagebox.showerror("Error", "Output folder does not exist.")
            return

        system = platform.system()
        try:
            if system == "Windows":
                subprocess.Popen(f'explorer "{path}"')
            elif system == "Linux":
                subprocess.Popen(["xdg-open", str(path)])
            else:
                messagebox.showinfo("Unsupported OS", f"Opening folder not supported on {system}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")


    def create_widgets(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # Input folder
        ttk.Label(frm, text="Input folder (MP3s):").pack(anchor=tk.W)
        input_frame = ttk.Frame(frm)
        input_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(input_frame, textvariable=self.input_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="Browse", command=self.browse_input).pack(side=tk.LEFT)

        # Output folder
        ttk.Label(frm, text="Output folder (Chapters):").pack(anchor=tk.W)
        output_frame = ttk.Frame(frm)
        output_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(output_frame, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side=tk.LEFT)

        # Model selector label
        ttk.Label(frm, text="Select Whisper Model:").pack(anchor=tk.W, pady=(0,4))

        # Model selector combobox
        self.model_var = tk.StringVar(value="base")
        model_combo = ttk.Combobox(frm, textvariable=self.model_var, state="readonly",
                           values=["tiny", "base", "small", "medium", "large"])
        model_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Start button
        self.start_btn = ttk.Button(frm, text="Start Splitting", command=self.start_splitting)
        self.start_btn.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(frm, mode="determinate")
        self.progress.pack(fill=tk.X, pady=5)

        # Log text area
        self.log_text = scrolledtext.ScrolledText(frm, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_label = ttk.Label(frm, textvariable=self.status_text)
        self.status_label.pack(anchor=tk.W, pady=2)

        # Open output folder button (hidden initially)
        self.open_folder_btn = ttk.Button(frm, text="Open Output Folder", command=self.open_output_folder)
        self.open_folder_btn.pack(pady=5, anchor=tk.E)
        self.open_folder_btn.pack_forget()  # Hide initially

        

    def browse_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_dir.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir.set(folder)

    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def sanitize_filename(self, s):
        s = s.strip()
        s = re.sub(r'[\\/*?:"<>|]', '_', s)
        s = re.sub(r'\s+', ' ', s)
        return s

    def start_splitting(self):
        self.open_folder_btn.pack_forget()  # Hide the button each time before starting
        input_path = self.input_dir.get()
        output_path = self.output_dir.get()
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select both input and output folders.")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.status_text.set("Loading model...")

        # Run splitting in background thread to keep UI responsive
        threading.Thread(target=self.split_audiobook, args=(Path(input_path), Path(output_path)), daemon=True).start()

    def split_audiobook(self, input_dir, output_dir):
        try:
            input_files = sorted(input_dir.glob("*.mp3"))
            if not input_files:
                self.log("No MP3 files found in input folder!")
                self.status_text.set("No MP3 files found.")
                self.start_btn.config(state=tk.NORMAL)
                return

            filelist_path = input_dir / "filelist.txt"
            with filelist_path.open("w", encoding="utf-8") as f:
                for mp3_file in input_files:
                    f.write(f"file '{mp3_file.as_posix()}'\n")

            combined_path = input_dir / "audiobook.wav"

            self.log("Combining MP3 files into audiobook.wav...")
            combine_cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0", "-i",
                str(filelist_path), "-c:a", "pcm_s16le", str(combined_path)
            ]
            result = subprocess.run(combine_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                self.log("Error combining files: " + result.stderr.decode())
                self.status_text.set("Error combining files")
                self.start_btn.config(state=tk.NORMAL)
                return
            self.log("Combine complete.\n")

            output_dir.mkdir(exist_ok=True)
            log_file = output_dir / "chapters_detected.txt"
            log_file.write_text("=== Chapter Detection Log ===\n\n")

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_choice = self.model_var.get()
            self.log(f"Loading Whisper model '{model_choice}'...")
            self.status_text.set(f"Loading Whisper model '{model_choice}'...")
            self.model = whisper.load_model(model_choice).to(device)

            self.chapter_counter = 1

            self.log(f"Processing {combined_path.name} ...")

            result = self.model.transcribe(str(combined_path))

            chapter_times = []
            chapter_names = []
            first_chapter = True

            with log_file.open("a", encoding="utf-8") as log:
                log.write(f"--- {combined_path.name} ---\n")
                for segment in result['segments']:
                    text = segment['text'].strip()
                    match = self.pattern.search(text)
                    if match:
                        start_time = 0.0 if first_chapter else segment['start']
                        first_chapter = False

                        chapter_times.append((self.chapter_counter, start_time))

                        # Extract only "Chapter X" if present
                        chapter_match = re.search(r'(Chapter\s+\d+)', text, re.IGNORECASE)
                        if chapter_match:
                            chapter_title = chapter_match.group(1)
                        else:
                            chapter_title = f"Chapter {self.chapter_counter}"

                        chapter_title = self.sanitize_filename(chapter_title)
                        chapter_names.append(chapter_title)

                        log.write(f"[{start_time:.2f}s] {text}\n")
                        self.log(f"Found chapter: {text}")
                        self.chapter_counter += 1
                log.write("\n")

            if not chapter_times:
                output_file = output_dir / "Full_Audiobook.wav"
                self.log("No chapters detected, saving full audiobook as one file.")
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(combined_path), "-c", "copy", str(output_file)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.status_text.set("Done!")
                self.start_btn.config(state=tk.NORMAL)
                return

            dur = result["segments"][-1]["end"]
            chapters_with_end = []
            for i, (num, start) in enumerate(chapter_times):
                end = chapter_times[i + 1][1] if i + 1 < len(chapter_times) else dur
                chapters_with_end.append((num, start, end))

            total_chapters = len(chapters_with_end)
            self.progress['maximum'] = total_chapters

            for idx, ((num, start, end), chapter_name) in enumerate(zip(chapters_with_end, chapter_names), 1):
                output_file = output_dir / f"{chapter_name}.wav"
                subprocess.run([
                    "ffmpeg",
                    "-y",
                    "-i", str(combined_path),
                    "-ss", str(start),
                    "-to", str(end),
                    "-c", "copy",
                    str(output_file)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.log(f"Saved chapter: {chapter_name}.wav")
                self.progress['value'] = idx
                self.status_text.set(f"Saved chapter {idx} of {total_chapters}")
            
            self.status_text.set("All chapters saved!")
            self.start_btn.config(state=tk.NORMAL)
            # Show the "Open Output Folder" button now
            self.open_folder_btn.pack()  # Show the button
            self.open_folder_btn.config(state=tk.NORMAL)
            try:
                combined_path.unlink()
                self.log("Deleted temporary combined file: audiobook.wav")
            except Exception as e:
                self.log(f"Could not delete audiobook.wav: {e}")
        except Exception as e:
            self.log(f"Error: {e}")
            self.status_text.set("Error occurred.")
            self.start_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    app = AudiobookSplitterApp()
    app.mainloop()
