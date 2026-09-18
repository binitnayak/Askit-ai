import streamlit as st
import os
from pypdf import PdfReader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from core.rag_engine import build_rag_chain, ask_question_stream
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import datetime

st.set_page_config(
    page_title="AskIt — Knowledge Chat",
    page_icon="💬",
    layout="centered"
)

st.title("💬 AskIt")
st.caption("Load a PDF, TXT file or YouTube video, then ask questions about it.")


# ── Helpers ──────────────────────────────────────────────────────────────────
def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        elif parsed.path.startswith(('/embed/', '/v/')):
            return parsed.path.split('/')[2]
    return None


def now_time():
    return datetime.datetime.now().strftime("%I:%M %p")


# ── State ─────────────────────────────────────────────────────────────────────
for key, val in {
    "vector_store": None,
    "active_source": None,
    "messages": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Source status ─────────────────────────────────────────────────────────────
if st.session_state.active_source:
    st.success(f"📎 Loaded: {st.session_state.active_source}")
else:
    st.info("No source loaded yet — upload a file or paste a YouTube link below.")

# ── Upload Panel ──────────────────────────────────────────────────────────────
with st.expander("📂 Load Source — PDF, TXT or YouTube", expanded=not st.session_state.active_source):

    tab1, tab2 = st.tabs(["📄 Document", "🎥 YouTube"])

    with tab1:
        uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
        if uploaded and st.session_state.active_source != uploaded.name:
            with st.spinner("Indexing document..."):
                text = ""
                if uploaded.name.endswith(".pdf"):
                    reader = PdfReader(uploaded)
                    for page in reader.pages:
                        text += page.extract_text() or ""
                else:
                    text = uploaded.read().decode("utf-8")

                if text.strip():
                    chunk_size, overlap = 300, 30
                    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]
                    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                    st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
                    st.session_state.active_source = uploaded.name
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"✅ **{uploaded.name}** loaded! {len(chunks)} chunks indexed. Ab poochh kuch bhi!",
                        "time": now_time()
                    })
                    st.rerun()
                else:
                    st.error("Could not extract text from this file.")

    with tab2:
        yt_url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")
        if st.button("▶️ Load Video", use_container_width=True):
            if yt_url:
                video_id = extract_video_id(yt_url)
                if video_id:
                    with st.spinner("Fetching transcript..."):
                        try:
                            try:
                                api = YouTubeTranscriptApi()
                                tlist = api.list(video_id)
                                t = None
                                for item in tlist:
                                    t = item.fetch()
                                    break
                                text = " ".join([i.text for i in t])
                            except Exception:
                                tlist = YouTubeTranscriptApi.get_transcript(video_id)
                                text = " ".join([i['text'] for i in tlist])

                            if text:
                                chunk_size, overlap = 300, 30
                                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]
                                embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                                st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
                                st.session_state.active_source = f"YT: {video_id}"
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"✅ YouTube video loaded! **{len(chunks)}** chunks indexed. Kuch bhi poochh!",
                                    "time": now_time()
                                })
                                st.rerun()
                            else:
                                st.error("No transcript found.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Invalid YouTube URL.")
            else:
                st.warning("Paste a YouTube URL first.")

st.divider()

# ── Chat History ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat Input ────────────────────────────────────────────────────────────────
if query := st.chat_input("Message AskIt..."):
    st.session_state.messages.append({"role": "user", "content": query, "time": now_time()})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        if st.session_state.vector_store is None:
            reply = "⚠️ Pehle koi document ya YouTube video load karo upar se!"
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply, "time": now_time()})
        else:
            rag_package = build_rag_chain(st.session_state.vector_store)
            response_gen = ask_question_stream(rag_package, query)
            full_response = st.write_stream(response_gen)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "time": now_time()})