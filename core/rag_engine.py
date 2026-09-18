import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "allam-2-7b",
]


def build_rag_chain(vector_store):
    """Returns retriever package."""
    return {"retriever": vector_store.as_retriever(search_kwargs={"k": 6})}


def get_relevant_docs(rag_package, query: str):
    """Fetch relevant chunks for a query — used to show sources separately."""
    retriever = rag_package["retriever"]
    return retriever.invoke(query)


def format_history(chat_history: list, max_turns: int = 3) -> str:
    """
    Turns the last few (user, bot) exchanges into a short text block
    so the model can understand follow-up questions like "isse aur explain karo".
    """
    if not chat_history:
        return "No previous conversation."

    recent = chat_history[-(max_turns * 2):]  # last N user+bot pairs
    lines = []
    for msg in recent:
        speaker = "User" if msg["role"] == "user" else "AskIt"
        lines.append(f"{speaker}: {msg['content']}")
    return "\n".join(lines)


def ask_question_stream(rag_package, query: str, chat_history: list = None):
    """Streams response using Groq API - fast & free!"""
    try:
        docs = get_relevant_docs(rag_package, query)
        context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No context found."
        history_text = format_history(chat_history or [])

        prompt = f"""You are AskIt, a helpful assistant that answers questions in detail using only the document context below.

Conversation so far (for understanding follow-up questions like "explain more" or "isse aur batao"):
{history_text}

Language rule (very important):
- Look at the language style of the CURRENT question below.
- If it's Hinglish (Hindi words in Roman/English script mixed with English), answer in the SAME natural Hinglish style.
- If it's plain English, answer in plain English.
- If it's pure Hindi (Devanagari), answer in pure Hindi.
- Match the question's language style exactly, every time — ignore the language of earlier turns.

Answer rules:
- If the current question refers back to the conversation (e.g. "iske baare mein aur batao", "what about the second point"), use the conversation history above to understand what "it" or "that" refers to.
- Give a thorough, well-explained answer using the document context — don't give a one-line reply unless the question genuinely only needs that.
- Structure longer answers with short paragraphs or a numbered/bulleted list when there are multiple points.
- Use only the information in the context below. If part of the answer isn't in the context, say clearly which part is missing, but still explain fully whatever IS supported.

Document context:
{context}

Current question: {query}

Answer:"""

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            yield "⚠️ GROQ_API_KEY missing in .env file!"
            return

        client = Groq(api_key=api_key)

        for model in GROQ_MODELS:
            try:
                print(f"🔄 Trying: {model}", flush=True)
                stream = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=2048,
                    stream=True,
                )

                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta

                print(f"✅ {model} worked!", flush=True)
                return

            except Exception as e:
                err = str(e)
                if "404" in err or "model_not_found" in err:
                    print(f"⏭️ {model} not available, trying next...", flush=True)
                    continue
                elif "429" in err or "rate_limit" in err:
                    print(f"⏭️ {model} rate limited, trying next...", flush=True)
                    continue
                else:
                    yield f"⚠️ Error: {err}"
                    return

        yield "⚠️ No models available. Check API key or try again."

    except Exception as e:
        yield f"⚠️ Error: {str(e)}"