import traceback
import sys

from app import (
    extract_text_from_pdf, 
    process_input, 
    transcribe_all, 
    generate_title, 
    summarize,
    extract_action_items,
    extract_key_decisions,
    extract_questions,
    build_rag_chain,
    ask_question
)

def run_test():
    try:
        source = "https://youtu.be/7HSSR1n8dgc?si=DnlGlgLjDOrdHyX5"
        
        print("Processing input...")
        chunks = process_input(source)
        print("Transcribing...")
        transcript = transcribe_all(chunks, "english")
        
        selected_model = "groq"
        print("Title...")
        title = generate_title(transcript, model_preference=selected_model)
        print("Summarize...")
        summary = summarize(transcript, model_preference=selected_model)
        
        print("Extracting...")
        action_items = extract_action_items(transcript, model_preference=selected_model)
        decisions = extract_key_decisions(transcript, model_preference=selected_model)
        questions = extract_questions(transcript, model_preference=selected_model)
        
        print("Building RAG...")
        rag_chain = build_rag_chain(transcript, model_preference=selected_model)
        
        print("Done!")
    except Exception as e:
        print(f"Exception caught: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
