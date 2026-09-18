import sys
from core.rag_engine import build_rag_chain, ask_question

print("Test script started", flush=True)

transcript = "This is a dummy transcript to test RAG. We talked about launching the new product next Tuesday."

print("Building RAG chain...", flush=True)
try:
    chain = build_rag_chain(transcript, model_preference="groq")
    print("RAG chain built successfully.", flush=True)
    
    print("Asking question...", flush=True)
    answer = ask_question(chain, "When are we launching?")
    print(f"Answer: {answer}", flush=True)
except Exception as e:
    import traceback
    traceback.print_exc()
