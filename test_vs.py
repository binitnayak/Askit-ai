from core.vector_store import build_vector_store
import sys

print("Testing vector store build...")
try:
    vs = build_vector_store("This is a test transcript.")
    print("Vector store built successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
