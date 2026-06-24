from typing import Dict, Any
from vector_store.faiss_db import model



def embed_node(state: Dict[str, Any]) -> Dict[str, Any]:
    chunks = state.get("chunks", [])
    vector_db = state.get("vector_db")  # 👈 REAL DB

    texts = []
    metadatas = []

    # 1. prepare text + metadata
    for node in chunks:
        if not isinstance(node, dict):
            continue

        text = " | ".join(
            node.get(k, "")
            for k in ["text", "title", "placeholder"]
            if node.get(k) and isinstance(node.get(k), str)
        )

        if text.strip():
            texts.append(text)
            metadatas.append(node)

    # 2. embed
    vectors = model.encode(texts)

    # 3. SAVE INTO VECTOR DB (THIS IS THE KEY PART)
    if vector_db is not None:
        vector_db.add_embeddings(
            texts=texts,
            embeddings=vectors,
            metadatas=metadatas
        )

    return {
        **state,
        "vector_db": vector_db,   # keep updated
        "embedding_nodes": [
            {"vector": v.tolist(), "metadata": m}
            for v, m in zip(vectors, metadatas)
        ]
    }