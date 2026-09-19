
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question


def run_pipeline(source: str, language: str = "english") -> dict:
    print("\n" + "=" * 60)
    print("🎬 STARTING AI VIDEO ASSISTANT")
    print("=" * 60)

    # Step 1: Process YouTube URL / local file
    print("\n📥 Processing input...")
    chunks = process_input(source)

    print(f"✅ Input processed: {len(chunks)} chunks")

    # Step 2: Transcription
    print("\n🎙️ Transcribing...")
    transcript = transcribe_all(chunks, language)

    print("\n📝 Raw transcription (first 300 characters):")
    print(transcript[:300])

    # Step 3: Generate title
    print("\n📌 Generating title...")
    title = generate_title(transcript)

    # Step 4: Generate summary
    print("\n📋 Generating summary...")
    summary = summarize(transcript)

    # Step 5: Extract action items
    print("\n✅ Extracting action items...")
    action_items = extract_action_items(transcript)

    # Step 6: Extract key decisions
    print("\n🔑 Extracting key decisions...")
    decisions = extract_key_decisions(transcript)

    # Step 7: Extract open questions
    print("\n❓ Extracting open questions...")
    questions = extract_questions(transcript)

    # Step 8: Build RAG chain
    print("\n🧠 Building RAG chain...")
    rag_chain = build_rag_chain(transcript)

    print("\n✅ AI Video Assistant pipeline completed!")

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


if __name__ == "__main__":

    # CLI entry point
    print("\n🎥 AI Video Assistant")

    source = input(
        "\nEnter YouTube URL or local file path: "
    ).strip()

    language = (
        input("Language (english/hinglish): ").strip()
        or "english"
    )

    result = run_pipeline(source, language)

    # =========================
    # DISPLAY RESULTS
    # =========================

    print("\n" + "=" * 60)
    print(f"📌 TITLE: {result['title']}")
    print("=" * 60)

    print(f"\n📋 SUMMARY:\n{result['summary']}")

    print("\n" + "=" * 60)
    print(f"✅ ACTION ITEMS:\n{result['action_items']}")

    print("\n" + "=" * 60)
    print(f"🔑 KEY DECISIONS:\n{result['key_decisions']}")

    print("\n" + "=" * 60)
    print(f"❓ OPEN QUESTIONS:\n{result['open_questions']}")

    print("\n" + "=" * 60)

    # =========================
    # PHASE 2 — RAG CHAT
    # =========================

    print("\n💬 Chat with your meeting")
    print("Type 'exit' to quit.\n")

    rag_chain = result["rag_chain"]

    while True:

        question = input("You: ").strip()

        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        if not question:
            continue

        try:
            answer = ask_question(rag_chain, question)
            print(f"\n🤖 Assistant: {answer}\n")

        except Exception as e:
            print(f"\n❌ Error while answering: {e}\n")
