

def embed_node(state):
    chunks = state.get("chunks", [])
    vector_db = state.get("vector_db")

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

    if vector_db and texts:
        vector_db.add_texts(
            texts=texts,
            metadatas=metadatas
        )

    return {
        **state,
        "vector_db": vector_db,
        "embedding_nodes": metadatas
    }