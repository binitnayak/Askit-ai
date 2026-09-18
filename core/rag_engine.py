# import requests
# import json

# def build_rag_chain(vector_store):
#     """Returns the retriever package with k=2 for better context."""
#     return {"retriever": vector_store.as_retriever(search_kwargs={"k": 2})}

# def ask_question_stream(rag_package, query: str):
#     """Streams response and handles reasoning models correctly."""
#     try:
#         retriever = rag_package["retriever"]
#         docs = retriever.invoke(query)
#         context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No context found."
        
#         prompt = f"""Answer the question in friendly Hinglish based on the context below. Keep it brief and direct.

# Context: {context}
# Question: {query}"""
        
#         url = "http://localhost:11434/api/generate"
#         payload = {
#             "model": "qwen3:4b",
#             "prompt": prompt,
#             "stream": True,
#             "options": {
#                 "temperature": 0.2,
#                 "num_predict": 2048,  # Increased significantly to allow thinking + output
#                 "num_ctx": 2048
#             }
#         }
        
#         response = requests.post(url, json=payload, stream=True, timeout=60)
        
#         if response.status_code == 200:
#             has_content = False
#             for line in response.iter_lines():
#                 if line:
#                     data = json.loads(line.decode('utf-8'))
#                     chunk = data.get("response", "")
#                     if chunk:
#                         has_content = True
#                         yield chunk
#             if not has_content:
#                 yield "⚠️ Ollama connected, but returned an empty response (Try increasing token limit or simplifying query)."
#         else:
#             yield f"⚠️ Ollama Error: Status code {response.status_code}"
            
#     except Exception as e:
#         yield f"⚠️ Error details: {str(e)}"


import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Tera actual Groq account ke available chat models
GROQ_MODELS = [
    "qwen/qwen3.8-27b",       # Best quality - smart model
    "openai/gpt-oss-20b",     # Fast + good
    "openai/gpt-oss-120b",    # Largest - best answers
    "allam-2-7b",             # Lightweight fallback
]


def build_rag_chain(vector_store):
    """Returns retriever package."""
    return {"retriever": vector_store.as_retriever(search_kwargs={"k": 3})}


def ask_question_stream(rag_package, query: str):
    """Streams response using Groq API - fast & free!"""
    try:
        # 1. Get relevant context
        retriever = rag_package["retriever"]
        docs = retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No context found."

        # 2. Build prompt
        prompt = f"""Answer the question in friendly Hinglish based on the context below.
Keep it brief, clear and helpful.

Context:
{context}

Question: {query}

Answer:"""

        # 3. Groq streaming
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
                    temperature=0.3,
                    max_tokens=1024,
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