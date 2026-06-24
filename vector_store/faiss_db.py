from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS

# load model
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_vector_db():
    # FAISS needs initial dummy data
    vector_db = FAISS.from_texts(
        ["init"],
        embedding=DummyEmbeddings()
    )

    return vector_db


class DummyEmbeddings:
    """
    Bridge class so FAISS works with SentenceTransformer
    """

    def embed_documents(self, texts):
        return model.encode(texts).tolist()

    def embed_query(self, text):
        return model.encode(text).tolist()