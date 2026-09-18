import traceback
from app import extract_text_from_pdf
from core.transcriber import transcribe_all
from utils.audio_processor import process_input

print("Testing imports successful.")

try:
    source = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Short video
    chunks = process_input(source)
    print(f"Chunks: {chunks}")
except Exception as e:
    print(f"Error in process_input: {e}")
    traceback.print_exc()

