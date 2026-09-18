import traceback

print("Importing HuggingFaceEmbeddings...")
from langchain_community.embeddings import HuggingFaceEmbeddings

print("Instantiating HuggingFaceEmbeddings...")
try:
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    print("Embeddings instantiated.")
    print("Embedding a test string...")
    res = embeddings.embed_query("test")
    print(f"Embedding successful, length: {len(res)}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

print("Importing Chroma...")
from langchain_chroma import Chroma
from langchain_core.documents import Document

print("Instantiating Chroma...")
try:
    doc = Document(page_content="test")
    vector_store = Chroma.from_documents(
        documents=[doc],
        embedding=embeddings,
        collection_name="test",
        persist_directory="test_db"
    )
    print("Chroma instantiated successfully.")
except Exception as e:
    print(f"Error in Chroma: {e}")
    traceback.print_exc()
