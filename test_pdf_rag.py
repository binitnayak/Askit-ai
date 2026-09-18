import traceback
import sys

from app import (
    generate_title, 
    summarize,
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question

def run_test():
    try:
        transcript = "This is a short meeting transcript. We decided to launch the product next week."
        selected_model = "groq"
        
        print("Title...")
        title = generate_title(transcript, model_preference=selected_model)
        
        print("Building RAG...")
        rag_chain = build_rag_chain(transcript, model_preference=selected_model)
        
        print("Asking question...")
        ans = ask_question(rag_chain, "What did we decide?", model_preference=selected_model)
        print(f"Answer: {ans}")
        print("Done!")
    except Exception as e:
        print(f"Exception caught: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
