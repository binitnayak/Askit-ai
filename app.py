# import streamlit as st
# import os
# from pypdf import PdfReader
# from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings
# from core.rag_engine import build_rag_chain, ask_question_stream
# from youtube_transcript_api import YouTubeTranscriptApi
# from urllib.parse import urlparse, parse_qs

# # Page Configuration
# st.set_page_config(
#     page_title="Knowledge Hub | Local AI Assistant",
#     page_icon="🧠",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # --- Custom Styling (CSS) ---
# st.markdown("""
#     <style>
#     .main-title {
#         font-size: 2.2rem;
#         font-weight: 700;
#         color: #1E293B;
#         margin-bottom: 0px;
#     }
#     .sub-title {
#         font-size: 1rem;
#         color: #64748B;
#         margin-bottom: 20px;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Helper function to extract YouTube Video ID
# def extract_video_id(url):
#     parsed_url = urlparse(url)
#     if parsed_url.hostname == 'youtu.be':
#         return parsed_url.path[1:]
#     if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
#         if parsed_url.path == '/watch':
#             return parse_qs(parsed_url.query).get('v', [None])[0]
#         elif parsed_url.path.startswith(('/embed/', '/v/')):
#             return parsed_url.path.split('/')[2]
#     return None

# # --- Sidebar ---
# with st.sidebar:
#     st.markdown("### 🛡️ Local Security")
#     st.info("Status: **100% Offline & Private**\nModel: `Qwen3:4b` (Ollama)")
    
#     st.divider()
#     st.markdown("### 📊 Active Context")
#     if "active_source" in st.session_state and st.session_state.active_source:
#         st.success(f"Loaded: **{st.session_state.active_source}**")
#     else:
#         st.warning("No source loaded yet.")
        
#     if st.button("🗑️ Clear Chat History", use_container_width=True):
#         st.session_state.messages = []
#         st.rerun()

# # --- Main Header ---
# st.markdown('<p class="main-title">🧠 Enterprise Knowledge Assistant</p>', unsafe_allow_html=True)
# st.markdown('<p class="sub-title">Chat securely with your local documents and video transcripts.</p>', unsafe_allow_html=True)

# # --- State Initialization ---
# if "vector_store" not in st.session_state:
#     st.session_state.vector_store = None
# if "active_source" not in st.session_state:
#     st.session_state.active_source = None
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # --- Tabs ---
# tab_doc, tab_yt = st.tabs(["📁 Documents & Notes", "🎥 YouTube Videos"])

# with tab_doc:
#     uploaded_file = st.file_uploader("Upload PDF or Text File", type=["pdf", "txt"])
#     if uploaded_file is not None:
#         if st.session_state.active_source != uploaded_file.name:
#             with st.spinner("🔄 Processing and indexing document locally..."):
#                 text = ""
#                 if uploaded_file.name.endswith(".pdf"):
#                     reader = PdfReader(uploaded_file)
#                     for page in reader.pages:
#                         text += page.extract_text() or ""
#                 else:
#                     text = uploaded_file.read().decode("utf-8")
                
#                 chunk_size = 300
#                 overlap = 30
#                 chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]
                
#                 embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
#                 st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
#                 st.session_state.active_source = uploaded_file.name
#                 st.success(f"✅ Successfully indexed: {uploaded_file.name}")

# with tab_yt:
#     yt_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
#     if st.button("Process Video"):
#         if yt_url:
#             video_id = extract_video_id(yt_url)
#             if video_id:
#                 with st.spinner("📥 Fetching transcript and indexing video..."):
#                     try:
#                         # Robust method to fetch transcripts across different API versions
#                         try:
#                             # Try modern list/fetch approach first
#                             api = YouTubeTranscriptApi()
#                             transcript_list = api.list(video_id)
#                             transcript = None
#                             for t in transcript_list:
#                                 transcript = t.fetch()
#                                 break
#                             text = " ".join([item.text for item in transcript])
#                         except Exception:
#                             # Fallback to direct get_transcript if available
#                             transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
#                             text = " ".join([item['text'] for item in transcript_list])
                        
#                         if text:
#                             chunk_size = 300
#                             overlap = 30
#                             chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]
                            
#                             embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
#                             st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
#                             st.session_state.active_source = f"YouTube: {video_id}"
#                             st.success("✅ YouTube video transcript indexed successfully!")
#                         else:
#                             st.error("⚠️ No transcripts found for this video.")
                            
#                     except Exception as e:
#                         st.error(f"Error fetching transcript: {e}. Make sure the video has captions enabled.")
#             else:
#                 st.warning("Invalid YouTube URL. Please check the link.")
#         else:
#             st.warning("Please enter a valid URL.")

# st.divider()

# # --- Chat Interface ---
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# if query := st.chat_input("Ask a question about your data..."):
#     st.session_state.messages.append({"role": "user", "content": query})
#     with st.chat_message("user"):
#         st.markdown(query)

#     with st.chat_message("assistant"):
#         if st.session_state.vector_store is not None:
#             rag_package = build_rag_chain(st.session_state.vector_store)
#             response_generator = ask_question_stream(rag_package, query)
#             response = st.write_stream(response_generator)
#         else:
#             response = "⚠️ Please upload a document or process a video from the tabs above first!"
#             st.markdown(response)
        
#         st.session_state.messages.append({"role": "assistant", "content": response})

import streamlit as st
import os
from pypdf import PdfReader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from core.rag_engine import build_rag_chain, ask_question_stream
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Knowledge Hub | Local AI Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 20px;
    }
    .stChatMessage { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)


# ── Helper: YouTube ID Extractor ──────────────────────────────────────────────
def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
    return None


# ── Session State Init ────────────────────────────────────────────────────────
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "active_source" not in st.session_state:
    st.session_state.active_source = None
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ Local Security")
    st.info("Status: **100% Offline & Private**\nModel: `Qwen3:4b` (Ollama)")

    st.divider()

    st.markdown("### 📊 Active Context")
    if st.session_state.active_source:
        st.success(f"Loaded: **{st.session_state.active_source}**")
    else:
        st.warning("No source loaded yet.")

    st.divider()

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🔄 Reset Everything", use_container_width=True):
        st.session_state.messages = []
        st.session_state.vector_store = None
        st.session_state.active_source = None
        st.rerun()

    st.divider()
    st.caption("💡 Make sure Ollama is running:\n`ollama serve`")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🧠 Enterprise Knowledge Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Chat securely with your local documents and video transcripts.</p>', unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_doc, tab_yt = st.tabs(["📁 Documents & Notes", "🎥 YouTube Videos"])

# ── Tab 1: Documents ──────────────────────────────────────────────────────────
with tab_doc:
    uploaded_file = st.file_uploader("Upload PDF or Text File", type=["pdf", "txt"])

    if uploaded_file is not None:
        if st.session_state.active_source != uploaded_file.name:
            with st.spinner("🔄 Processing and indexing document..."):
                text = ""
                if uploaded_file.name.endswith(".pdf"):
                    reader = PdfReader(uploaded_file)
                    for page in reader.pages:
                        text += page.extract_text() or ""
                else:
                    text = uploaded_file.read().decode("utf-8")

                if text.strip():
                    chunk_size = 300
                    overlap = 30
                    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

                    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                    st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
                    st.session_state.active_source = uploaded_file.name
                    st.success(f"✅ Indexed: **{uploaded_file.name}** ({len(chunks)} chunks)")
                else:
                    st.error("❌ Could not extract text from this file.")

# ── Tab 2: YouTube ────────────────────────────────────────────────────────────
with tab_yt:
    yt_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("▶️ Process Video"):
        if yt_url:
            video_id = extract_video_id(yt_url)
            if video_id:
                with st.spinner("📥 Fetching transcript and indexing..."):
                    try:
                        # Try modern API first, fallback to legacy
                        try:
                            api = YouTubeTranscriptApi()
                            transcript_list = api.list(video_id)
                            transcript = None
                            for t in transcript_list:
                                transcript = t.fetch()
                                break
                            text = " ".join([item.text for item in transcript])
                        except Exception:
                            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                            text = " ".join([item['text'] for item in transcript_list])

                        if text:
                            chunk_size = 300
                            overlap = 30
                            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

                            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                            st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
                            st.session_state.active_source = f"YouTube: {video_id}"
                            st.success(f"✅ Indexed YouTube video! ({len(chunks)} chunks)")
                        else:
                            st.error("⚠️ No transcript found for this video.")

                    except Exception as e:
                        st.error(f"❌ Error: {e}\n\nMake sure the video has captions enabled.")
            else:
                st.warning("⚠️ Invalid YouTube URL. Please check the link.")
        else:
            st.warning("⚠️ Please enter a YouTube URL first.")

st.divider()

# ── Chat Interface ────────────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        if st.session_state.vector_store is not None:
            rag_package = build_rag_chain(st.session_state.vector_store)
            response_generator = ask_question_stream(rag_package, query)
            response = st.write_stream(response_generator)
        else:
            response = "⚠️ Please upload a document or process a YouTube video first!"
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})