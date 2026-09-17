import streamlit as st
from dotenv import load_dotenv
import time
from fpdf import FPDF
from io import BytesIO
import re

load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question

# ────────────────────────────────────────────────
# Page Config
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────
# Custom CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg: #07070c;
    --surface: #0f0f17;
    --surface-2: #161622;
    --border: #252535;
    --accent: #8b5cf6;
    --accent-light: #a78bfa;
    --cyan: #22d3ee;
    --text: #f1f1f6;
    --text-muted: #8888a8;
    --success: #34d399;
    --danger: #f87171;
}

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(139, 92, 246, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(139, 92, 246, 0.025) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    z-index: 0;
}
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text) !important;
    font-weight: 700 !important;
}
.hero h1 {
    font-size: 2.6rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #fff 0%, #a78bfa 45%, #22d3ee 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem 0 !important;
}
.hero p {
    color: var(--text-muted);
    font-size: 0.85rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0;
}
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    position: relative;
}
.card::before {
    content: '';
    position: absolute;
    left: 0; top: 14px; bottom: 14px;
    width: 3px;
    border-radius: 0 4px 4px 0;
    background: linear-gradient(180deg, var(--accent), var(--cyan));
}
.card-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.7rem;
}
.card-body {
    font-size: 0.92rem;
    line-height: 1.7;
    color: var(--text);
}
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
}
.pill-info {
    background: rgba(139, 92, 246, 0.12);
    color: var(--accent-light);
    border: 1px solid rgba(139, 92, 246, 0.25);
}
.pill-error {
    background: rgba(248, 113, 113, 0.1);
    color: var(--danger);
    border: 1px solid rgba(248, 113, 113, 0.25);
}
.pill-success {
    background: rgba(52, 211, 153, 0.1);
    color: var(--success);
    border: 1px solid rgba(52, 211, 153, 0.25);
}
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 30px rgba(124, 58, 237, 0.35) !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent), var(--cyan)) !important;
}
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# PDF Helpers
# ────────────────────────────────────────────────
def extract_text_from_pdf(uploaded_file) -> str:
    from pypdf import PdfReader
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n\n"
    return text.strip()


class MeetingPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 120)
        self.cell(0, 8, "AI Video Assistant - Meeting Report", align="R")
        self.ln(4)
        self.set_draw_color(139, 92, 246)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 160)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(124, 58, 237)
        self.cell(0, 10, title, ln=True)
        self.ln(1)

    def section_body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 40)
        clean = re.sub(r'[^\x00-\x7F]+', ' ', str(text))
        self.multi_cell(0, 6, clean)
        self.ln(4)


def generate_pdf(result: dict) -> bytes:
    pdf = MeetingPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 20, 30)
    title_clean = re.sub(r'[^\x00-\x7F]+', ' ', result["title"])
    pdf.multi_cell(0, 10, title_clean)
    pdf.ln(6)

    pdf.section_title("Summary")
    pdf.section_body(result["summary"])

    pdf.section_title("Action Items")
    pdf.section_body(result["action_items"])

    pdf.section_title("Key Decisions")
    pdf.section_body(result["key_decisions"])

    pdf.section_title("Open Questions")
    pdf.section_body(result["open_questions"])

    pdf.add_page()
    pdf.section_title("Full Content")
    pdf.section_body(result["transcript"])

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


# ────────────────────────────────────────────────
# Session State
# ────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ────────────────────────────────────────────────
# Sidebar
# ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <div style="font-size:1.6rem; font-weight:800; background: linear-gradient(135deg,#fff,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            🎬 AI Video
        </div>
        <div style="font-size:0.7rem; color:#8888a8; letter-spacing:0.15em; text-transform:uppercase; margin-top:2px;">
            Meeting Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    input_type = st.radio(
        "Input Type",
        options=["YouTube / Audio / Video", "PDF Document"],
        index=0,
    )

    source = None
    uploaded_pdf = None
    language = "english"

    if input_type == "YouTube / Audio / Video":
        st.markdown("**YouTube URL or File Path**")
        source = st.text_input(
            "Source",
            placeholder="https://youtu.be/... or C:/videos/meeting.mp4",
            label_visibility="collapsed",
        )
        language = st.selectbox("Language", options=["english", "hinglish"], index=0)
    else:
        st.markdown("**Upload PDF**")
        uploaded_pdf = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            label_visibility="collapsed",
        )

    st.markdown("")
    run_btn = st.button("⚡  Analyse", use_container_width=True)

    if st.session_state.result:
        st.markdown("---")
        st.markdown('<span class="pill pill-success">✓ Pipeline Completed</span>', unsafe_allow_html=True)
        st.markdown("")
        if st.button("🔄  New Analysis", use_container_width=True):
            st.session_state.result = None
            st.session_state.chat_history = []
            st.rerun()

# ────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>AI Video Assistant</h1>
    <p>Transcribe · Summarise · Extract · Chat · PDF Support</p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────
if run_btn:
    st.session_state.result = None
    st.session_state.chat_history = []

    progress = st.progress(0)
    status = st.empty()

    try:
        transcript = ""

        # PDF Mode
        if input_type == "PDF Document":
            if not uploaded_pdf:
                st.error("Please upload a PDF file.")
                st.stop()

            status.markdown('<span class="pill pill-info">📄 Extracting text from PDF...</span>', unsafe_allow_html=True)
            progress.progress(20)
            transcript = extract_text_from_pdf(uploaded_pdf)

            if not transcript or len(transcript.strip()) < 50:
                st.error("Could not extract enough text from this PDF. It may be scanned/image-based.")
                st.stop()

        # YouTube / Audio / Video Mode
        else:
            if not source or not source.strip():
                st.error("Please enter a YouTube URL or local file path.")
                st.stop()

            status.markdown('<span class="pill pill-info">📥 Processing input...</span>', unsafe_allow_html=True)
            progress.progress(10)
            chunks = process_input(source.strip())

            status.markdown('<span class="pill pill-info">🎙️ Transcribing audio...</span>', unsafe_allow_html=True)
            progress.progress(30)
            transcript = transcribe_all(chunks, language)

        # Common Pipeline
        status.markdown('<span class="pill pill-info">📌 Generating title...</span>', unsafe_allow_html=True)
        progress.progress(50)
        title = generate_title(transcript)

        status.markdown('<span class="pill pill-info">📋 Generating summary...</span>', unsafe_allow_html=True)
        progress.progress(65)
        summary = summarize(transcript)

        status.markdown('<span class="pill pill-info">✅ Extracting action items...</span>', unsafe_allow_html=True)
        progress.progress(78)
        action_items = extract_action_items(transcript)

        status.markdown('<span class="pill pill-info">🔑 Extracting key decisions...</span>', unsafe_allow_html=True)
        progress.progress(86)
        decisions = extract_key_decisions(transcript)

        status.markdown('<span class="pill pill-info">❓ Extracting open questions...</span>', unsafe_allow_html=True)
        progress.progress(93)
        questions = extract_questions(transcript)

        status.markdown('<span class="pill pill-info">🧠 Building RAG engine...</span>', unsafe_allow_html=True)
        progress.progress(98)
        rag_chain = build_rag_chain(transcript)

        progress.progress(100)
        status.markdown('<span class="pill pill-success">✓ Analysis completed!</span>', unsafe_allow_html=True)

        st.session_state.result = {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }

        time.sleep(0.5)
        progress.empty()
        status.empty()
        st.rerun()

    except Exception as e:
        progress.empty()
        status.markdown(f'<span class="pill pill-error">✕ {str(e)}</span>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Results
# ────────────────────────────────────────────────
if st.session_state.result:
    result = st.session_state.result

    st.markdown(f"### {result['title']}")
    st.markdown("")

    col1, col2 = st.columns([1.25, 1], gap="large")

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-label">📋 Summary</div>
            <div class="card-body">{result['summary']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <div class="card-label">✅ Action Items</div>
            <div class="card-body">{result['action_items']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <div class="card-label">🔑 Key Decisions</div>
            <div class="card-body">{result['key_decisions']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <div class="card-label">❓ Open Questions</div>
            <div class="card-body">{result['open_questions']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-label">📝 Full Content</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("View Full Content", expanded=False):
            st.text_area("Content", value=result["transcript"], height=350, label_visibility="collapsed")

        st.markdown("#### 📥 Export Report")

        report_txt = f"""# {result['title']}

## Summary
{result['summary']}

## Action Items
{result['action_items']}

## Key Decisions
{result['key_decisions']}

## Open Questions
{result['open_questions']}

## Full Content
{result['transcript']}
"""
        st.download_button(
            "⬇️ Download TXT",
            data=report_txt,
            file_name=f"{result['title'][:40].replace(' ', '_')}_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

        try:
            pdf_bytes = generate_pdf(result)
            st.download_button(
                "📄 Download PDF",
                data=pdf_bytes,
                file_name=f"{result['title'][:40].replace(' ', '_')}_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"PDF generation failed: {e}")

    # Chat
    st.markdown("---")
    st.markdown("### 💬 Chat with your Document / Meeting")
    st.caption("Answers are generated only from the uploaded content.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything about this content..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = ask_question(result["rag_chain"], prompt)
                    st.markdown(answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    err = f"Error: {str(e)}"
                    st.error(err)
                    st.session_state.chat_history.append({"role": "assistant", "content": err})

else:
    st.markdown("""
    <div style="margin-top: 1.5rem; padding: 2rem; background: #0f0f17; border: 1px solid #252535; border-radius: 14px;">
        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.8rem;">Get started</div>
        <div style="color: #8888a8; font-size: 0.95rem; line-height: 1.7;">
            Choose <b>YouTube / Audio / Video</b> or <b>PDF Document</b> from the sidebar and click 
            <span style="color:#a78bfa; font-weight:600;">Analyse</span>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("#### What this tool does")
    st.markdown("""
    - 🎙️ Transcribes **English / Hindi / Hinglish** meetings  
    - 📄 Supports **PDF upload** + chat with PDF  
    - 📋 Generates clean professional summary  
    - ✅ Extracts **Action Items**  
    - 🔑 Extracts **Key Decisions**  
    - ❓ Finds **Open Questions**  
    - 💬 **Chat** using RAG  
    - 📄 Export as **PDF** or TXT  
    """)