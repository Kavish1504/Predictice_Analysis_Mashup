import os
import sys
import shutil
import subprocess
import imageio_ffmpeg as ffmpeg
from yt_dlp import YoutubeDL

# Parsing Arguments
if len(sys.argv) != 5:
    print("Usage:")
    print("python program.py <SingerName> <NumberOfVideos(10 or more)> <AudioDuration(20 or more)> <OutputFileName>")
    sys.exit(1)

SINGER_NAME = sys.argv[1]
N = int(sys.argv[2])       
Y = int(sys.argv[3])          
FINAL_OUTPUT = sys.argv[4]

if N < 10:
    print("Number of videos must be at least 10.")
    sys.exit(1)

if Y < 20:
    print("Audio duration must be at least 20 seconds.")
    sys.exit(1)

DOWNLOAD_DIR = "downloads"
AUDIO_DIR = "audio"
CUT_DIR = "cut_audio"

os.makedirs(DOWNLOAD_DIR, exist_ok = True)
os.makedirs(AUDIO_DIR, exist_ok = True)
os.makedirs(CUT_DIR, exist_ok = True)
FFMPEG_PATH = ffmpeg.get_ffmpeg_exe()

def clean_workspace():
    for folder in ["downloads", "audio", "cut_audio"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    if os.path.exists(FINAL_OUTPUT):
        os.remove(FINAL_OUTPUT)

# Downloading Videos
def download_videos(singer, n):
    search_query = f"ytsearch{n}:{singer} songs"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "extractor_args": {"youtube": {"player_client": ["android"]}},
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])

# Converting videos to audios
def convert_to_audio():
    for file in os.listdir(DOWNLOAD_DIR):
        input_path = os.path.join(DOWNLOAD_DIR, file)
        output_path = os.path.join(
            AUDIO_DIR, os.path.splitext(file)[0] + ".mp3"
        )
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", input_path, "-vn", "-ab", "192k", output_path],
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL
        )

# Cutting audio to Y seconds
def cut_audio():
    files = os.listdir(AUDIO_DIR)
    if not files:
        print("ERROR: No audio files found to cut!")
        return
    
    print(f"Cutting {len(files)} audio files to {Y} seconds...")
    for file in files:
        input_path = os.path.join(AUDIO_DIR, file)
        output_path = os.path.join(CUT_DIR, file)
        result = subprocess.run([
            FFMPEG_PATH, "-y", "-i", input_path,
            "-t", str(Y),
            "-acodec", "copy",
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Cut: {file}")
        else:
            print(f"Failed: {file}")

# Merging all audios
def merge_audio(final_output):
    files = sorted(os.listdir(CUT_DIR))
    if not files:
        print("ERROR: No files found in cut_audio directory")
        return
    
    print(f"Found {len(files)} files to merge")
    list_file = "files.txt"
    with open(list_file, "w", encoding = "utf-8") as f:
        for file in files:
            # Use forward slashes and escape path properly
            file_path = os.path.join(CUT_DIR, file).replace("\\", "/")
            f.write(f"file '{file_path}'\n")
            print(f"  - {file}")
    
    print("Running FFmpeg merge")
    result = subprocess.run([
        FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        final_output
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"FFmpeg Error: {result.stderr}")
    else:
        print(f"Merge successful!")
    
    if os.path.exists(list_file):
        os.remove(list_file)

def main():
    clean_workspace()
    os.makedirs(DOWNLOAD_DIR, exist_ok = True)
    os.makedirs(AUDIO_DIR, exist_ok = True)
    os.makedirs(CUT_DIR, exist_ok = True)
    print(f"Singer       : {SINGER_NAME}")
    print(f"Videos       : {N}")
    print(f"Duration     : {Y} seconds")
    print(f"Output File  : {FINAL_OUTPUT}")
    download_videos(SINGER_NAME, N)
    convert_to_audio()
    cut_audio()
    merge_audio(FINAL_OUTPUT)
    
    # Verify output file was created
    if os.path.exists(FINAL_OUTPUT):
        file_size = os.path.getsize(FINAL_OUTPUT) / (1024 * 1024)  # Size in MB
        print(f"SUCCESS! Final merged file saved as: {FINAL_OUTPUT}")
        print(f"File size: {file_size:.2f} MB")
    else:
        print(f"ERROR! Output file was not created: {FINAL_OUTPUT}")
        sys.exit(1)

if __name__ == "__main__":
    main()