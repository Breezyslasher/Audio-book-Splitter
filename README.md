# Description
This program is used to split large audiobooks into individual chapters. The tool uses OpenAI's Whisper to find any mention of the word chapter with a number preceding it, 
like chapter 20 or chapter ten

## Requirements 
Python IdLE  

Whisper 


Torch 


tkinter
## Setup

### 1. Install Python
 https://www.python.org/downloads/
 
### 2. Install Required Python Packages
pip install torch tqdm git+https://github.com/openai/whisper.git

### 3. Install FFmpeg
The script uses FFmpeg to combine and split audio files.

Linux:

    sudo apt install ffmpeg

Windows:
 
 
Download FFmpeg from https://ffmpeg.org/download.html and add it to your PATH environment variable.

Mac:

    brew install ffmpeg

Verify FFmpeg is installed:

ffmpeg -version
