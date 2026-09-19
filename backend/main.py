
import io
import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
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


# =========================================================
# ENV
# =========================================================

load_dotenv()


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="AskIt API")


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


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "askit.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source_type TEXT,
            source_name TEXT,
            source_id TEXT,
            source_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (conversation_id)
            REFERENCES conversations(id)
            ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


# =========================================================
# GLOBAL VECTOR STORE
# =========================================================

vector_store = None
active_conversation_id = None


# =========================================================
# MODELS
# =========================================================

class YouTubeRequest(BaseModel):
    video_id: str
    conversation_id: int | None = None


class ChatRequest(BaseModel):
    question: str
    conversation_id: int


class ConversationRequest(BaseModel):
    title: str = "New Chat"


# =========================================================
# EMBEDDINGS + SPLITTER
# =========================================================

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)


splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " ", ""],
)


# =========================================================
# VECTOR STORE
# =========================================================

def create_vector_store(text: str):
    global vector_store

    if not text or not text.strip():
        raise Exception("Document text is empty.")

    chunks = splitter.split_text(text)

    if not chunks:
        raise Exception("Could not create text chunks.")

    vector_store = FAISS.from_texts(
        chunks,
        embeddings
    )

    return len(chunks)


# =========================================================
# CONVERSATION HELPERS
# =========================================================

def create_conversation(
    title="New Chat",
    source_type=None,
    source_name=None,
    source_id=None,
    source_text=None,
):
    now = datetime.now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO conversations
        (
            title,
            source_type,
            source_name,
            source_id,
            source_text,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            source_type,
            source_name,
            source_id,
            source_text,
            now,
            now,
        ),
    )

    conversation_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return conversation_id


def update_conversation_source(
    conversation_id,
    source_type,
    source_name,
    source_id,
    source_text,
):
    now = datetime.now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET
            source_type = ?,
            source_name = ?,
            source_id = ?,
            source_text = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            source_type,
            source_name,
            source_id,
            source_text,
            now,
            conversation_id,
        ),
    )

    conn.commit()
    conn.close()


def update_title(conversation_id, title):
    now = datetime.now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET title = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            title,
            now,
            conversation_id,
        ),
    )

    conn.commit()
    conn.close()


@app.put("/conversations/{conversation_id}/rename")
def rename_conversation(conversation_id: int, data: dict):
    title = data.get("title", "").strip()

    if not title:
        return {
            "success": False,
            "error": "Title cannot be empty."
        }

    update_title(conversation_id, title)

    return {
        "success": True,
        "conversation_id": conversation_id,
        "title": title
    }


def save_message(
    conversation_id,
    role,
    content,
):
    now = datetime.now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (
            conversation_id,
            role,
            content,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
            now,
        ),
    )

    cursor.execute(
        """
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ?
        """,
        (
            now,
            conversation_id,
        ),
    )

    conn.commit()
    conn.close()


def get_messages(conversation_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            role,
            content,
            created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,),
    )

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_conversation(conversation_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)

    return None


# =========================================================
# HOME / HEALTH
# =========================================================

@app.get("/")
def home():
    return {
        "message": "AskIt Backend is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# =========================================================
# CREATE NEW CONVERSATION
# =========================================================

@app.post("/conversations")
def new_conversation(request: ConversationRequest):
    conversation_id = create_conversation(
        title=request.title or "New Chat"
    )

    return {
        "success": True,
        "conversation_id": conversation_id,
        "title": request.title or "New Chat",
    }


# =========================================================
# GET ALL CONVERSATIONS
# =========================================================

@app.get("/conversations")
def get_all_conversations():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            source_type,
            source_name,
            created_at,
            updated_at
        FROM conversations
        ORDER BY updated_at DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        "success": True,
        "conversations": [
            dict(row)
            for row in rows
        ],
    }


# =========================================================
# GET ONE CONVERSATION
# =========================================================

@app.get("/conversations/{conversation_id}")
def get_one_conversation(conversation_id: int):
    global vector_store
    global active_conversation_id

    conversation = get_conversation(
        conversation_id
    )

    if not conversation:
        return {
            "success": False,
            "error": "Conversation not found."
        }

    # Restore source into vector store
    if conversation["source_text"]:
        create_vector_store(
            conversation["source_text"]
        )

    active_conversation_id = conversation_id

    messages = get_messages(
        conversation_id
    )

    return {
        "success": True,
        "conversation": conversation,
        "messages": messages,
    }


# =========================================================
# DELETE CONVERSATION
# =========================================================

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int):
    global vector_store
    global active_conversation_id

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE conversation_id = ?
        """,
        (conversation_id,),
    )

    cursor.execute(
        """
        DELETE FROM conversations
        WHERE id = ?
        """,
        (conversation_id,),
    )

    conn.commit()
    conn.close()

    if active_conversation_id == conversation_id:
        vector_store = None
        active_conversation_id = None

    return {
        "success": True,
        "message": "Conversation deleted."
    }


# =========================================================
# YOUTUBE
# =========================================================

@app.post("/youtube")
def get_youtube_transcript(
    request: YouTubeRequest
):
    global active_conversation_id

    try:

        if not request.video_id.strip():
            return {
                "success": False,
                "error": "YouTube video ID is empty."
            }

        conversation_id = request.conversation_id

        # If frontend didn't provide conversation
        # create one automatically
        if conversation_id is None:
            conversation_id = create_conversation(
                title="YouTube Chat"
            )

        api = YouTubeTranscriptApi()

        try:

            transcript_list = api.list(
                request.video_id
            )

            try:

                transcript = transcript_list.find_transcript(
                    ["hi", "en"]
                )

                fetched = transcript.fetch()

            except Exception:

                fetched = None

                for transcript in transcript_list:

                    try:

                        fetched = transcript.fetch()

                        if fetched:
                            break

                    except Exception:
                        continue

                if not fetched:
                    raise Exception(
                        "No usable transcript found."
                    )

        except IpBlocked:

            return {
                "success": False,
                "error": (
                    "YouTube is blocking requests from your IP. "
                    "The transcript library is installed correctly."
                )
            }

        except RequestBlocked:

            return {
                "success": False,
                "error": (
                    "YouTube blocked the transcript request."
                )
            }

        except TranscriptsDisabled:

            return {
                "success": False,
                "error": (
                    "This video has transcripts disabled."
                )
            }

        except NoTranscriptFound:

            return {
                "success": False,
                "error": (
                    "No transcript was found for this video."
                )
            }

        except VideoUnavailable:

            return {
                "success": False,
                "error": (
                    "This YouTube video is unavailable."
                )
            }

        transcript_parts = []

        for item in fetched:

            if hasattr(item, "text"):

                transcript_parts.append(
                    item.text
                )

            elif isinstance(item, dict):

                text_value = item.get("text")

                if text_value:
                    transcript_parts.append(
                        str(text_value)
                    )

            elif isinstance(item, (tuple, list)):

                if len(item) > 0:
                    transcript_parts.append(
                        str(item[0])
                    )

        text = " ".join(
            transcript_parts
        )

        if not text.strip():
            raise Exception(
                "Transcript is empty."
            )

        chunks_count = create_vector_store(
            text
        )

        update_conversation_source(
            conversation_id=conversation_id,
            source_type="youtube",
            source_name=f"YouTube: {request.video_id}",
            source_id=request.video_id,
            source_text=text,
        )

        update_title(
            conversation_id,
            f"YouTube: {request.video_id}"
        )

        active_conversation_id = conversation_id

        return {
            "success": True,
            "conversation_id": conversation_id,
            "video_id": request.video_id,
            "source_type": "youtube",
            "chunks": chunks_count,
            "message": (
                "YouTube transcript loaded "
                "and indexed successfully."
            ),
        }

    except Exception as e:

        print(
            "YouTube Error:",
            str(e)
        )

        return {
            "success": False,
            "error": str(e)
        }


# =========================================================
# PDF / TXT
# =========================================================

@app.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: int | None = Form(None),
):

    global active_conversation_id

    try:

        if not file.filename:

            return {
                "success": False,
                "error": "No file selected."
            }

        filename = file.filename.lower()

        if not (
            filename.endswith(".pdf")
            or filename.endswith(".txt")
        ):

            return {
                "success": False,
                "error": (
                    "Only PDF and TXT files are supported."
                ),
            }

        file_bytes = await file.read()

        if not file_bytes:

            return {
                "success": False,
                "error": "Uploaded file is empty."
            }

        # Create conversation if needed
        if conversation_id is None:

            conversation_id = create_conversation(
                title=file.filename
            )

        # TXT
        if filename.endswith(".txt"):

            try:

                text = file_bytes.decode(
                    "utf-8"
                )

            except UnicodeDecodeError:

                text = file_bytes.decode(
                    "latin-1"
                )

        # PDF
        else:

            try:

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

        if not text.strip():

            return {
                "success": False,
                "error": (
                    "No readable text found "
                    "inside this document."
                ),
            }

        chunks_count = create_vector_store(
            text
        )

        source_type = (
            "pdf"
            if filename.endswith(".pdf")
            else "txt"
        )

        update_conversation_source(
            conversation_id=conversation_id,
            source_type=source_type,
            source_name=file.filename,
            source_id=None,
            source_text=text,
        )

        update_title(
            conversation_id,
            file.filename
        )

        active_conversation_id = conversation_id

        return {
            "success": True,
            "conversation_id": conversation_id,
            "filename": file.filename,
            "source_type": source_type,
            "chunks": chunks_count,
            "message": (
                "Document loaded and indexed successfully."
            ),
        }

    except Exception as e:

        print(
            "Document Error:",
            str(e)
        )

        return {
            "success": False,
            "error": str(e)
        }


# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(request: ChatRequest):

    global vector_store
    global active_conversation_id

    try:

        conversation = get_conversation(
            request.conversation_id
        )

        if not conversation:

            return {
                "success": False,
                "error": "Conversation not found."
            }

        # Restore vector store if needed
        if (
            vector_store is None
            or active_conversation_id
            != request.conversation_id
        ):

            if conversation["source_text"]:

                create_vector_store(
                    conversation["source_text"]
                )

                active_conversation_id = (
                    request.conversation_id
                )

            else:

                return {
                    "success": False,
                    "error": (
                        "Pehle koi YouTube video "
                        "ya document load karo."
                    ),
                }

        question = request.question.strip()

        if not question:

            return {
                "success": False,
                "error": "Question empty hai."
            }

        # Get old messages from SQLite
        old_messages = get_messages(
            request.conversation_id
        )

        chat_history = [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in old_messages
        ]

        rag_package = build_rag_chain(
            vector_store
        )

        response_generator = ask_question_stream(
            rag_package,
            question,
            chat_history=chat_history,
        )

        answer = "".join(
            response_generator
        )

        # Save user message
        save_message(
            request.conversation_id,
            "user",
            question,
        )

        # Save AI message
        save_message(
            request.conversation_id,
            "assistant",
            answer,
        )

        # Automatically create title
        if len(old_messages) == 0:

            title = question[:45]

            if len(question) > 45:
                title += "..."

            update_title(
                request.conversation_id,
                title,
            )

        return {
            "success": True,
            "answer": answer,
            "conversation_id": (
                request.conversation_id
            ),
        }

    except Exception as e:

        print(
            "Chat Error:",
            str(e)
        )

        return {
            "success": False,
            "error": str(e)
        }