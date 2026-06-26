from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

_vector_db = None


def create_vector_db():
    global _vector_db
    index = faiss.IndexFlatL2(384)  # MiniLM dimension
    _vector_db = FAISS(
        embedding_function=embedding_model,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={}
    )
    return _vector_db


def get_vector_db():
    """Get the global vector DB instance."""
    if _vector_db is None:
        raise RuntimeError("Vector DB not initialized. Call create_vector_db() first.")
    return _vector_db