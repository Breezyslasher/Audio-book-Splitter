# Description
This program is used to split large audiobooks into individual chapters. The tool uses OpenAI's Whisper to find any mention of the word chapter with a number preceding it, 
like chapter 20 or chapter ten

## Setup

### 1. Install Python
Make sure you have Python 3.8 or newer installed on your system.

    https://www.python.org/downloads/

Verify installation:

    python --version

 
 
### 2. Install Required Python Packages
The script needs:

whisper (OpenAI’s Whisper ASR model)

torch (PyTorch for running Whisper)

tqdm (progress bar)

Install them with:

    pip install torch tqdm git+https://github.com/openai/whisper.git

Note:

For GPU support, install the correct PyTorch version from pytorch.org matching your CUDA version 

On CPU-only machines, the above will install CPU PyTorch.

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

### 4. Prepare Your Audiobook Files

Place all your MP3 audiobook files in a single folder (e.g., ./audiobook_mp3s).

### 5. Run the Script
When the script is run for the first time, it will download the whisper model.

## Troubleshooting

###1. Slow Download of Model
You can manually download the model from https://github.com/openai/whisper/blob/main/whisper/__init__.py 


Put the downloaded model in
    
    Windows: C:\Users\<username>\.cache\whisper\<model>
    Linux: /home/<username>/.cache/whisper/<model>

