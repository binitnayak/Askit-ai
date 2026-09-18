# import os
# import time
# from dotenv import load_dotenv
# from groq import Groq
# from concurrent.futures import ThreadPoolExecutor

# load_dotenv()

# WHISPER_MODEL = "whisper-large-v3-turbo"


# def transcribe_chunk_groq(chunk_path: str, client: Groq) -> str:
#     try:
#         print(f"⏳ Processing {os.path.basename(chunk_path)}...", flush=True)
#         start_time = time.time()
        
#         with open(chunk_path, "rb") as file:
#             transcription = client.audio.transcriptions.create(
#                 file=(os.path.basename(chunk_path), file.read()),
#                 model=WHISPER_MODEL,
#                 response_format="text"
#             )
        
#         elapsed = round(time.time() - start_time, 2)
#         print(f"✅ Chunk finished in {elapsed}s", flush=True)
#         return str(transcription)
#     except Exception as e:
#         print(f"❌ Error transcribing {chunk_path}: {e}", flush=True)
#         return ""
#     finally:
#         if os.path.exists(chunk_path):
#             os.remove(chunk_path)


# def transcribe_all(chunks: list, language: str = "english") -> str:
#     api_key = os.getenv("GROQ_API_KEY")
#     if not api_key:
#         raise ValueError("GROQ_API_KEY is missing in .env file.")

#     client = Groq(api_key=api_key, timeout=30.0)
#     print(f"⚡ Parallel Transcribing {len(chunks)} chunk(s) using Groq Whisper...", flush=True)

#     results = [None] * len(chunks)

#     def process(idx_path):
#         idx, path = idx_path
#         text = transcribe_chunk_groq(path, client)
#         return idx, text

#     with ThreadPoolExecutor(max_workers=min(5, len(chunks))) as executor:
#         futures = [executor.submit(process, (i, chunk)) for i, chunk in enumerate(chunks)]
#         for future in futures:
#             idx, text = future.result()
#             results[idx] = text

#     print("✓ Transcription complete.", flush=True)
#     return " ".join(filter(None, results)).strip()

import os
import time
from dotenv import load_dotenv
from groq import Groq
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

WHISPER_MODEL = "whisper-large-v3-turbo"


def transcribe_chunk_groq(chunk_path: str, client: Groq) -> str:
    """Transcribes a single audio chunk using Groq Whisper API."""
    try:
        print(f"⏳ Processing {os.path.basename(chunk_path)}...", flush=True)
        start_time = time.time()

        with open(chunk_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(chunk_path), file.read()),
                model=WHISPER_MODEL,
                response_format="text"
            )

        elapsed = round(time.time() - start_time, 2)
        print(f"✅ Chunk done in {elapsed}s", flush=True)
        return str(transcription)

    except Exception as e:
        print(f"❌ Error transcribing {chunk_path}: {e}", flush=True)
        return ""
    finally:
        # Clean up chunk file after processing
        if os.path.exists(chunk_path):
            os.remove(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:
    """Parallel transcription of all audio chunks."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing in .env file.")

    client = Groq(api_key=api_key, timeout=30.0)
    print(f"⚡ Parallel Transcribing {len(chunks)} chunk(s) using Groq Whisper...", flush=True)

    results = [None] * len(chunks)

    def process(idx_path):
        idx, path = idx_path
        text = transcribe_chunk_groq(path, client)
        return idx, text

    with ThreadPoolExecutor(max_workers=min(5, len(chunks))) as executor:
        futures = [executor.submit(process, (i, chunk)) for i, chunk in enumerate(chunks)]
        for future in futures:
            idx, text = future.result()
            results[idx] = text

    print("✓ Transcription complete.", flush=True)
    return " ".join(filter(None, results)).strip()