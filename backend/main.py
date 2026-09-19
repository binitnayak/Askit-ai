from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    IpBlocked,
    RequestBlocked,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pypdf import PdfReader

from core.rag_engine import (
    build_rag_chain,
    ask_question_stream,
)

import os
from dotenv import load_dotenv


# ==================================================
# LOAD ENV
# ==================================================

load_dotenv()


# ==================================================
# APP
# ==================================================

app = FastAPI(title="AskIt API")


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# GLOBAL VECTOR STORE
# ==================================================

vector_store = None


# ==================================================
# CHAT HISTORY
# ==================================================

chat_history = []


# ==================================================
# REQUEST MODELS
# ==================================================

class YouTubeRequest(BaseModel):
    video_id: str


class ChatRequest(BaseModel):
    question: str


# ==================================================
# EMBEDDINGS
# ==================================================

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)


# ==================================================
# TEXT CHUNKER
# ==================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        "",
    ],
)


# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():
    return {
        "message": "AskIt Backend is running!"
    }


# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ==================================================
# HELPER
# ==================================================

def create_vector_store(text: str):
    """
    Convert text into chunks
    and create FAISS vector store.
    """

    global vector_store

    if not text or not text.strip():
        raise Exception(
            "Document text is empty."
        )

    # --------------------------------------------------
    # Create chunks
    # --------------------------------------------------

    chunks = splitter.split_text(text)

    if not chunks:
        raise Exception(
            "Could not create text chunks."
        )

    print(
        f"📚 Creating {len(chunks)} chunks...",
        flush=True,
    )

    # --------------------------------------------------
    # Create FAISS
    # --------------------------------------------------

    vector_store = FAISS.from_texts(
        chunks,
        embeddings,
    )

    print(
        "✅ FAISS vector store created.",
        flush=True,
    )

    return len(chunks)


# ==================================================
# YOUTUBE TRANSCRIPT
# ==================================================

@app.post("/youtube")
def get_youtube_transcript(
    request: YouTubeRequest
):

    global vector_store
    global chat_history

    try:

        # --------------------------------------------------
        # Reset old conversation
        # --------------------------------------------------

        chat_history = []

        # --------------------------------------------------
        # Validate video ID
        # --------------------------------------------------

        video_id = request.video_id.strip()

        if not video_id:

            return {
                "success": False,
                "error": "YouTube video ID is empty.",
            }

        print(
            f"🎬 Loading YouTube video: {video_id}",
            flush=True,
        )

        # ==================================================
        # PROXY CONFIGURATION
        # ==================================================

        proxy_username = os.getenv(
            "YOUTUBE_PROXY_USERNAME"
        )

        proxy_password = os.getenv(
            "YOUTUBE_PROXY_PASSWORD"
        )

        # --------------------------------------------------
        # If proxy credentials exist
        # --------------------------------------------------

        if proxy_username and proxy_password:

            from youtube_transcript_api.proxies import (
                WebshareProxyConfig
            )

            proxy_config = WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )

            api = YouTubeTranscriptApi(
                proxy_config=proxy_config
            )

            print(
                "🌐 YouTube proxy enabled.",
                flush=True,
            )

        # --------------------------------------------------
        # Without proxy
        # --------------------------------------------------

        else:

            api = YouTubeTranscriptApi()

            print(
                "🌐 YouTube proxy not configured.",
                flush=True,
            )

        # ==================================================
        # GET TRANSCRIPT LIST
        # ==================================================

        transcript_list = api.list(
            video_id
        )

        # ==================================================
        # TRY HINDI / ENGLISH
        # ==================================================

        try:

            transcript = transcript_list.find_transcript(
                ["hi", "en"]
            )

            fetched = transcript.fetch()

        except NoTranscriptFound:

            # --------------------------------------------------
            # Try any available transcript
            # --------------------------------------------------

            fetched = None

            for transcript in transcript_list:

                try:

                    fetched = transcript.fetch()

                    if fetched:
                        break

                except Exception:
                    continue

            if not fetched:

                raise NoTranscriptFound(
                    video_id,
                    ["hi", "en"],
                    transcript_list,
                )

        # ==================================================
        # CONVERT TRANSCRIPT TO TEXT
        # ==================================================

        transcript_parts = []

        for item in fetched:

            # --------------------------------------------------
            # New API object format
            # --------------------------------------------------

            if hasattr(item, "text"):

                transcript_parts.append(
                    item.text
                )

            # --------------------------------------------------
            # Dictionary format
            # --------------------------------------------------

            elif isinstance(item, dict):

                text_value = item.get(
                    "text"
                )

                if text_value:

                    transcript_parts.append(
                        str(text_value)
                    )

            # --------------------------------------------------
            # Tuple / list format
            # --------------------------------------------------

            elif isinstance(
                item,
                (tuple, list)
            ):

                if len(item) > 0:

                    transcript_parts.append(
                        str(item[0])
                    )

        # --------------------------------------------------
        # Combine transcript
        # --------------------------------------------------

        text = " ".join(
            transcript_parts
        )

        if not text.strip():

            raise Exception(
                "Transcript is empty."
            )

        print(
            f"✅ Transcript loaded: {len(text)} characters",
            flush=True,
        )

        # ==================================================
        # CREATE VECTOR STORE
        # ==================================================

        chunks_count = create_vector_store(
            text
        )

        print(
            "✅ YouTube transcript indexed successfully.",
            flush=True,
        )

        # ==================================================
        # SUCCESS
        # ==================================================

        return {
            "success": True,
            "video_id": video_id,
            "source_type": "youtube",
            "chunks": chunks_count,
            "message": (
                "YouTube transcript loaded "
                "and indexed successfully."
            ),
        }

    # ==================================================
    # YOUTUBE IP BLOCK
    # ==================================================

    except IpBlocked:

        print(
            "❌ YouTube IP is blocked.",
            flush=True,
        )

        return {
            "success": False,
            "error": (
                "YouTube is blocking transcript "
                "requests from this IP."
            ),
            "error_type": "ip_blocked",
        }

    # ==================================================
    # REQUEST BLOCK
    # ==================================================

    except RequestBlocked:

        print(
            "❌ YouTube request was blocked.",
            flush=True,
        )

        return {
            "success": False,
            "error": (
                "YouTube blocked the transcript "
                "request. Please try again later "
                "or configure a supported proxy."
            ),
            "error_type": "request_blocked",
        }

    # ==================================================
    # TRANSCRIPTS DISABLED
    # ==================================================

    except TranscriptsDisabled:

        print(
            "❌ Transcripts are disabled.",
            flush=True,
        )

        return {
            "success": False,
            "error": (
                "This YouTube video has "
                "transcripts disabled."
            ),
            "error_type": "transcripts_disabled",
        }

    # ==================================================
    # NO TRANSCRIPT
    # ==================================================

    except NoTranscriptFound:

        print(
            "❌ No transcript found.",
            flush=True,
        )

        return {
            "success": False,
            "error": (
                "No transcript was found "
                "for this YouTube video."
            ),
            "error_type": "no_transcript",
        }

    # ==================================================
    # VIDEO UNAVAILABLE
    # ==================================================

    except VideoUnavailable:

        print(
            "❌ YouTube video unavailable.",
            flush=True,
        )

        return {
            "success": False,
            "error": (
                "This YouTube video is unavailable."
            ),
            "error_type": "video_unavailable",
        }

    # ==================================================
    # OTHER YOUTUBE ERROR
    # ==================================================

    except Exception as e:

        print(
            "❌ YouTube Error:",
            str(e),
            flush=True,
        )

        return {
            "success": False,
            "error": str(e),
            "error_type": "unknown",
        }


# ==================================================
# PDF / TXT DOCUMENT
# ==================================================

@app.post("/document")
async def upload_document(
    file: UploadFile = File(...)
):

    global vector_store
    global chat_history

    try:

        # --------------------------------------------------
        # Reset old conversation
        # --------------------------------------------------

        chat_history = []

        # --------------------------------------------------
        # Validate filename
        # --------------------------------------------------

        if not file.filename:

            return {
                "success": False,
                "error": "No file selected.",
            }

        filename = file.filename.lower()

        # --------------------------------------------------
        # Only PDF / TXT
        # --------------------------------------------------

        if not (
            filename.endswith(".pdf")
            or filename.endswith(".txt")
        ):

            return {
                "success": False,
                "error": (
                    "Only PDF and TXT files "
                    "are supported."
                ),
            }

        # --------------------------------------------------
        # Read file
        # --------------------------------------------------

        file_bytes = await file.read()

        if not file_bytes:

            return {
                "success": False,
                "error": "Uploaded file is empty.",
            }

        # ==================================================
        # TXT
        # ==================================================

        if filename.endswith(".txt"):

            try:

                text = file_bytes.decode(
                    "utf-8"
                )

            except UnicodeDecodeError:

                text = file_bytes.decode(
                    "latin-1"
                )

        # ==================================================
        # PDF
        # ==================================================

        else:

            try:

                import io

                pdf_file = io.BytesIO(
                    file_bytes
                )

                reader = PdfReader(
                    pdf_file
                )

                pages = []

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:

                        pages.append(
                            page_text
                        )

                text = "\n\n".join(
                    pages
                )

            except Exception as e:

                raise Exception(
                    f"Could not read PDF: {str(e)}"
                )

        # --------------------------------------------------
        # Validate extracted text
        # --------------------------------------------------

        if not text.strip():

            return {
                "success": False,
                "error": (
                    "No readable text found "
                    "inside this document."
                ),
            }

        print(
            f"📄 Processing document: {file.filename}",
            flush=True,
        )

        # --------------------------------------------------
        # Create vector store
        # --------------------------------------------------

        chunks_count = create_vector_store(
            text
        )

        # --------------------------------------------------
        # Source type
        # --------------------------------------------------

        source_type = (
            "pdf"
            if filename.endswith(".pdf")
            else "txt"
        )

        print(
            "✅ Document indexed successfully.",
            flush=True,
        )

        return {
            "success": True,
            "filename": file.filename,
            "source_type": source_type,
            "chunks": chunks_count,
            "message": (
                "Document loaded and "
                "indexed successfully."
            ),
        }

    except Exception as e:

        print(
            "❌ Document Error:",
            str(e),
            flush=True,
        )

        return {
            "success": False,
            "error": str(e),
        }


# ==================================================
# CHAT
# ==================================================

@app.post("/chat")
def chat(request: ChatRequest):

    global vector_store
    global chat_history

    try:

        # --------------------------------------------------
        # Check source
        # --------------------------------------------------

        if vector_store is None:

            return {
                "success": False,
                "error": (
                    "Pehle koi YouTube video "
                    "ya document load karo."
                ),
            }

        # --------------------------------------------------
        # Check question
        # --------------------------------------------------

        question = request.question.strip()

        if not question:

            return {
                "success": False,
                "error": "Question empty hai.",
            }

        print(
            f"💬 Question: {question}",
            flush=True,
        )

        # --------------------------------------------------
        # Build RAG
        # --------------------------------------------------

        rag_package = build_rag_chain(
            vector_store
        )

        # --------------------------------------------------
        # Ask question
        # --------------------------------------------------

        response_generator = ask_question_stream(
            rag_package,
            question,
            chat_history=chat_history,
        )

        # --------------------------------------------------
        # Generator → complete answer
        # --------------------------------------------------

        answer = "".join(
            response_generator
        )

        # --------------------------------------------------
        # Save user message
        # --------------------------------------------------

        chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        # --------------------------------------------------
        # Save assistant message
        # --------------------------------------------------

        chat_history.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        # --------------------------------------------------
        # Keep last 20 messages
        # --------------------------------------------------

        if len(chat_history) > 20:

            chat_history = chat_history[-20:]

        print(
            "✅ Answer generated.",
            flush=True,
        )

        # --------------------------------------------------
        # Return answer
        # --------------------------------------------------

        return {
            "success": True,
            "answer": answer,
        }

    except Exception as e:

        print(
            "❌ Chat Error:",
            str(e),
            flush=True,
        )

        return {
            "success": False,
            "error": str(e),
        }