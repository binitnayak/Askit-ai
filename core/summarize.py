# import os
# from concurrent.futures import ThreadPoolExecutor
# from dotenv import load_dotenv

# load_dotenv()

# # Sirf active aur latest Groq models
# GROQ_MODELS = [
#     "llama-3.3-70b-versatile",
#     "llama-3.1-8b-instant"
# ]

# GEMINI_MODEL = "gemini-1.5-flash"


# def call_groq(prompt: str) -> str:
#     from groq import Groq

#     api_key = os.getenv("GROQ_API_KEY")
#     if not api_key:
#         raise ValueError("GROQ_API_KEY missing in .env")

#     client = Groq(api_key=api_key)

#     for model in GROQ_MODELS:
#         try:
#             response = client.chat.completions.create(
#                 model=model,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.3,
#             )
#             return response.choices[0].message.content
#         except Exception as e:
#             print(f"⚠️ Groq model '{model}' error: {e}, trying next...", flush=True)
#             continue

#     raise RuntimeError("All active Groq models failed.")


# def call_gemini(prompt: str) -> str:
#     from google import genai

#     api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
#     if not api_key:
#         raise ValueError("GEMINI_API_KEY missing in .env")

#     client = genai.Client(api_key=api_key)
#     response = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=prompt,
#     )
#     return response.text


# def query_llm(prompt: str) -> str:
#     try:
#         return call_groq(prompt)
#     except Exception as e:
#         print(f"⚠️ Groq failed, attempting Gemini fallback...", flush=True)
#         try:
#             return call_gemini(prompt)
#         except Exception as ge:
#             print(f"❌ Gemini fallback failed: {ge}", flush=True)
#             return "Unable to generate response. Groq/Gemini limit or server issue."


# def summarize(transcript: str) -> str:
#     prompt = f"Provide a concise executive summary of the following transcript:\n\n{transcript}"
#     return query_llm(prompt)


# def generate_title(transcript: str) -> str:
#     prompt = f"Generate a short, engaging title (max 5 words) for this transcript:\n\n{transcript}"
#     res = query_llm(prompt)
#     return res.strip().strip('"')


# def extract_action_items(transcript: str) -> str:
#     prompt = f"Extract all action items, assignees, and deadlines in bullet points:\n\n{transcript}"
#     return query_llm(prompt)


# def extract_key_decisions(transcript: str) -> str:
#     prompt = f"Extract all key decisions made in this transcript:\n\n{transcript}"
#     return query_llm(prompt)


# def extract_questions(transcript: str) -> str:
#     prompt = f"List all open questions or discussion points from this transcript:\n\n{transcript}"
#     return query_llm(prompt)


# def summarize_transcript(transcript: str) -> dict:
#     print("🎬 Parallel extracting Summary & Insights...", flush=True)
#     with ThreadPoolExecutor(max_workers=4) as executor:
#         f_sum = executor.submit(summarize, transcript)
#         f_act = executor.submit(extract_action_items, transcript)
#         f_dec = executor.submit(extract_key_decisions, transcript)
#         f_que = executor.submit(extract_questions, transcript)

#     return {
#         "summary": f_sum.result(),
#         "action_items": f_act.result(),
#         "key_decisions": f_dec.result(),
#         "questions": f_que.result(),
#     }

import os
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ============ MODELS ============
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]
GEMINI_MODEL = "gemini-1.5-flash"  # Fixed: was gemini-3.6-flash (doesn't exist)


# ============ LLM CALLERS ============
def call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY missing in .env")

    client = Groq(api_key=api_key)

    for model in GROQ_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq model '{model}' error: {e}, trying next...", flush=True)
            continue

    raise RuntimeError("All active Groq models failed.")


def call_gemini(prompt: str) -> str:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY missing in .env")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text


def query_llm(prompt: str) -> str:
    """Primary LLM caller: Groq → Gemini fallback."""
    try:
        return call_groq(prompt)
    except Exception as e:
        print(f"⚠️ Groq failed, attempting Gemini fallback...", flush=True)
        try:
            return call_gemini(prompt)
        except Exception as ge:
            print(f"❌ Gemini fallback failed: {ge}", flush=True)
            return "Unable to generate response. Groq/Gemini limit or server issue."


# ============ CORE FUNCTIONS ============
def summarize(transcript: str) -> str:
    prompt = f"Provide a concise executive summary of the following transcript:\n\n{transcript}"
    return query_llm(prompt)


def generate_title(transcript: str) -> str:
    prompt = f"Generate a short, engaging title (max 5 words) for this transcript:\n\n{transcript}"
    res = query_llm(prompt)
    return res.strip().strip('"')


def extract_action_items(transcript: str) -> str:
    prompt = f"Extract all action items, assignees, and deadlines in bullet points:\n\n{transcript}"
    return query_llm(prompt)


def extract_key_decisions(transcript: str) -> str:
    prompt = f"Extract all key decisions made in this transcript:\n\n{transcript}"
    return query_llm(prompt)


def extract_questions(transcript: str) -> str:
    prompt = f"List all open questions or discussion points from this transcript:\n\n{transcript}"
    return query_llm(prompt)


def summarize_transcript(transcript: str) -> dict:
    """Parallel extraction of all insights at once."""
    print("🎬 Parallel extracting Summary & Insights...", flush=True)
    with ThreadPoolExecutor(max_workers=4) as executor:
        f_sum = executor.submit(summarize, transcript)
        f_act = executor.submit(extract_action_items, transcript)
        f_dec = executor.submit(extract_key_decisions, transcript)
        f_que = executor.submit(extract_questions, transcript)

    return {
        "summary": f_sum.result(),
        "action_items": f_act.result(),
        "key_decisions": f_dec.result(),
        "questions": f_que.result(),
    }