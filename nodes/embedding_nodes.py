

from vector_store.faiss_db import get_vector_db


def embed_node(state):
    print("==========embed_node=============")
    chunks = state.get("chunks", [])
    vector_db = get_vector_db()

    texts = []
    metadatas = []

    for node in chunks:
        text = " | ".join(
            node.get(k, "")
            for k in ["text", "title", "placeholder"]
            if node.get(k)
        )

        if text.strip():
            texts.append(text)
            metadatas.append(node)

    if texts:
        vector_db.add_texts(
            texts=texts,
            metadatas=metadatas
        )

    return {
        **state,
    }