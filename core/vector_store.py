# import os
# import shutil
# from typing import Optional
# from langchain_chroma import Chroma 
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_core.documents import Document

# CHROMA_DIR = "vector_db"
# COLLECTION_NAME = "meeting_transcript"
# EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# # Singleton cache for embedding model
# _embedding_instance = None


# def get_embeddings() -> HuggingFaceEmbeddings:
#     """Cache embedding model in memory to avoid repeated CPU load delays."""
#     global _embedding_instance
#     if _embedding_instance is None:
#         _embedding_instance = HuggingFaceEmbeddings(
#             model_name=EMBEDDING_MODEL,
#             model_kwargs={"device": "cpu"}
#         )
#     return _embedding_instance


# def build_vector_store(transcript: str) -> Chroma:
#     """Cleans previous DB and builds fresh Chroma vector store from transcript."""
    
#     # 1. Clear old vector database to avoid mixing previous meeting contexts
#     if os.path.exists(CHROMA_DIR):
#         try:
#             shutil.rmtree(CHROMA_DIR)
#             print("🧹 Old vector database cleaned.")
#         except Exception as e:
#             print(f"⚠️ Could not clear old vector_db: {e}")

#     print("⚡ Building new vector store...")

#     # 2. Optimal chunking for full sentences and meeting context retention
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=150
#     )
#     chunks = splitter.split_text(transcript)

#     docs = [
#         Document(page_content=chunk, metadata={'chunk_index': i})
#         for i, chunk in enumerate(chunks)
#     ]

#     embeddings = get_embeddings()
#     vector_store = Chroma.from_documents(
#         documents=docs,
#         embedding=embeddings,
#         collection_name=COLLECTION_NAME,
#         persist_directory=CHROMA_DIR
#     )

#     return vector_store


# def load_vector_store() -> Optional[Chroma]:
#     """Loads existing Chroma vector store safely."""
#     if not os.path.exists(CHROMA_DIR):
#         print("⚠️ Vector database directory does not exist.")
#         return None

#     embeddings = get_embeddings()
#     vector_store = Chroma(
#         collection_name=COLLECTION_NAME,
#         embedding_function=embeddings,
#         persist_directory=CHROMA_DIR
#     )

#     return vector_store


# def get_retriever(vector_store: Chroma, k: int = 3):
#     """Returns MMR (Maximal Marginal Relevance) retriever to reduce chunk redundancy."""
#     return vector_store.as_retriever(
#         search_type="mmr",
#         search_kwargs={"k": k, "lambda_mult": 0.7}
#     )

import os
import shutil
from typing import Optional
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Singleton cache - avoids reloading model every time
_embedding_instance = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embedding_instance
    if _embedding_instance is None:
        print("⚡ Loading embedding model (first time only)...", flush=True)
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"}
        )
    return _embedding_instance


def build_vector_store(transcript: str) -> Chroma:
    """Clears old DB and builds fresh Chroma store from transcript."""

    if os.path.exists(CHROMA_DIR):
        try:
            shutil.rmtree(CHROMA_DIR)
            print("🧹 Old vector database cleared.", flush=True)
        except Exception as e:
            print(f"⚠️ Could not clear old vector_db: {e}", flush=True)

    print("⚡ Building new vector store...", flush=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={"chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR
    )

    print(f"✅ Vector store ready: {len(chunks)} chunks indexed.", flush=True)
    return vector_store


def load_vector_store() -> Optional[Chroma]:
    """Loads existing Chroma store if available."""
    if not os.path.exists(CHROMA_DIR):
        print("⚠️ Vector database not found.", flush=True)
        return None

    embeddings = get_embeddings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )


def get_retriever(vector_store: Chroma, k: int = 3):
    """MMR retriever - reduces redundant chunks."""
    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "lambda_mult": 0.7}
    )