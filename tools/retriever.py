# def retrieve(query: str, vector_db, k: int = 5):
#     results = vector_db.similarity_search(query, k=k)
#     return [r.page_content for r in results]



def retrieve(query, vector_db, k=5):
    docs = vector_db.similarity_search(query, k=k)

    results = []

    for doc in docs:
        results.append({
            "text": doc.page_content,
            "metadata": doc.metadata
        })

    return results