def retrieve(query: str, vector_db, k: int = 5):
    results = vector_db.similarity_search(query, k=k)
    return [r.page_content for r in results]