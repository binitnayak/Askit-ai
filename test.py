
from dotenv import load_dotenv

# Load environment variables before importing core modules
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)


# =========================
# INPUT
# =========================

source = "https://youtu.be/BvHVVvTIIm8?si=SV_iz_iel1tIzDN8"

# "english"  -> Whisper
# "hinglish" -> Sarvam
language = "english"


# =========================
# PROCESS AUDIO / VIDEO
# =========================

print("\n" + "=" * 60)
print("🎬 PROCESSING INPUT")
print("=" * 60)

chunks = process_input(source)

print(f"✅ Input processed successfully")
print(f"📦 Total chunks: {len(chunks)}")


# =========================
# TRANSCRIPTION
# =========================

print("\n" + "=" * 60)
print("🎙️ TRANSCRIBING")
print("=" * 60)

transcript = transcribe_all(
    chunks,
    language=language
)

print("✅ Transcription completed")

print("\n" + "=" * 60)
print("📝 TRANSCRIPT")
print("=" * 60)

print(
    transcript[:500] + "..."
    if len(transcript) > 500
    else transcript
)


# =========================
# TITLE
# =========================

print("\n" + "=" * 60)
print("📌 GENERATING TITLE")
print("=" * 60)

title = generate_title(transcript)

print(f"📌 TITLE: {title}")


# =========================
# SUMMARY
# =========================

print("\n" + "=" * 60)
print("📋 GENERATING SUMMARY")
print("=" * 60)

summary = summarize(transcript)

print("\n📋 SUMMARY")
print("-" * 60)
print(summary)


# =========================
# ACTION ITEMS
# =========================

print("\n" + "=" * 60)
print("✅ EXTRACTING ACTION ITEMS")
print("=" * 60)

action_items = extract_action_items(transcript)

print(action_items)


# =========================
# KEY DECISIONS
# =========================

print("\n" + "=" * 60)
print("🔑 EXTRACTING KEY DECISIONS")
print("=" * 60)

decisions = extract_key_decisions(transcript)

print(decisions)


# =========================
# OPEN QUESTIONS
# =========================

print("\n" + "=" * 60)
print("❓ EXTRACTING OPEN QUESTIONS")
print("=" * 60)

questions = extract_questions(transcript)

print(questions)


# =========================
# DONE
# =========================

print("\n" + "=" * 60)
print("🎉 VIDEO AGENT COMPLETED SUCCESSFULLY")
print("=" * 60)