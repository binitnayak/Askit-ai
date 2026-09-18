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


def ask_question_stream(rag_package, query: str):
    """Streams response using Groq API - fast & free!"""
    try:
        retriever = rag_package["retriever"]
        docs = retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No context found."

        prompt = f"""You are AskIt, a helpful assistant that answers questions in detail using only the context below.

Language rule (very important):
- Look at the language style of the QUESTION below.
- If the question is written in Hinglish (Hindi words in Roman/English script, mixed with English), answer in the SAME natural Hinglish style — like a friend explaining something.
- If the question is written in plain English, answer in plain, natural English.
- If the question is written in pure Hindi (Devanagari script), answer in pure Hindi.
- Match the question's language style exactly, every time.

Answer rules:
- Give a thorough, well-explained answer — don't just give a one-line reply. Explain the reasoning, cover every relevant point found in the context, and use examples from the context where helpful.
- Structure longer answers with short paragraphs or a numbered/bulleted list when there are multiple points.
- Use only the information in the context below. If part of the answer isn't in the context, say clearly which part is missing, but still explain fully whatever the context DOES support — don't cut the answer short just because some detail is missing.
- Never respond with just one or two sentences unless the question genuinely only needs that.

Context:
{context}

Question: {query}

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

