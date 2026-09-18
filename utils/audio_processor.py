# import os
# import re
# import yt_dlp
# from pydub import AudioSegment


# def is_youtube_url(url: str) -> bool:
#     youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
#     return bool(re.match(youtube_regex, url))


# def download_youtube_audio(youtube_url: str, output_dir: str = "temp") -> str:
#     """Downloads YouTube audio in low-size MP3 format bypassing bot blocks."""
#     os.makedirs(output_dir, exist_ok=True)
#     output_template = os.path.join(output_dir, "yt_download.%(ext)s")

#     ydl_opts = {
#         "format": "bestaudio/best",
#         "outtmpl": output_template,
#         "postprocessors": [
#             {
#                 "key": "FFmpegExtractAudio",
#                 "preferredcodec": "mp3",
#                 "preferredquality": "128",
#             }
#         ],
#         "quiet": True,
#         "no_warnings": True,
#         "extractor_args": {
#             "youtube": {
#                 "player_client": ["android", "ios"]
#             }
#         },
#     }

#     print("⏬ Downloading YouTube Audio (Fast MP3)...", flush=True)
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         ydl.extract_info(youtube_url, download=True)
#         return os.path.join(output_dir, "yt_download.mp3")


# def chunk_audio(audio_path: str, chunk_length_ms: int = 3 * 60 * 1000) -> list:
#     """Splits audio into 3-minute MP3 chunks (<5MB per chunk for instant upload)."""
#     print("✂️ Chunking audio...", flush=True)
#     audio = AudioSegment.from_file(audio_path)
#     chunks = []
    
#     for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
#         chunk = audio[start : start + chunk_length_ms]
#         chunk_path = f"{audio_path}_chunk_{i}.mp3"
#         chunk.export(chunk_path, format="mp3", bitrate="128k")
#         chunks.append(chunk_path)
        
#     print(f"✓ Audio ready: {len(chunks)} chunk(s) created.", flush=True)
#     return chunks


# def process_input(input_source: str) -> list:
#     if is_youtube_url(input_source):
#         audio_path = download_youtube_audio(input_source)
#     else:
#         audio_path = input_source

#     return chunk_audio(audio_path)

import os
import re
import yt_dlp
from pydub import AudioSegment


def is_youtube_url(url: str) -> bool:
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    return bool(re.match(youtube_regex, url))


def download_youtube_audio(youtube_url: str, output_dir: str = "temp") -> str:
    """Downloads YouTube audio as MP3, bypasses bot blocks via android/ios client."""
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, "yt_download.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        },
    }

    print("⏬ Downloading YouTube Audio...", flush=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(youtube_url, download=True)
        return os.path.join(output_dir, "yt_download.mp3")


def chunk_audio(audio_path: str, chunk_length_ms: int = 3 * 60 * 1000) -> list:
    """Splits audio into 3-minute chunks (< 5MB each for Groq API limit)."""
    print("✂️ Chunking audio...", flush=True)
    audio = AudioSegment.from_file(audio_path)
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start: start + chunk_length_ms]
        chunk_path = f"{audio_path}_chunk_{i}.mp3"
        chunk.export(chunk_path, format="mp3", bitrate="128k")
        chunks.append(chunk_path)

    print(f"✓ {len(chunks)} chunk(s) ready.", flush=True)
    return chunks


def process_input(input_source: str) -> list:
    """Main entry point: YouTube URL or local file → list of audio chunks."""
    if is_youtube_url(input_source):
        audio_path = download_youtube_audio(input_source)
    else:
        audio_path = input_source

    return chunk_audio(audio_path)