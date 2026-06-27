

import json

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

# ---------------- EMBEDDINGS ----------------
    with open("output/embeddings.txt", "w", encoding="utf-8") as f:
    # index_to_docstore_id maps FAISS internal int index -> docstore id
        for i, docstore_id in vector_db.index_to_docstore_id.items():
            doc = vector_db.docstore.search(docstore_id)
            vector = vector_db.index.reconstruct(i)  # numpy array, shape (dim,)
            f.write(f"\n--- EMBEDDING {i+1} ---\n")
            f.write("META:\n")
            f.write(json.dumps(doc.metadata, ensure_ascii=False, indent=2) + "\n\n")
            f.write("TEXT:\n")
            f.write(doc.page_content + "\n\n")
            f.write("VECTOR (first 10 dims):\n")
            f.write(str(vector[:10].tolist()) + "\n")
            f.write(f"VECTOR DIM: {len(vector)}\n")    

    return {
        **state,
    }