from typing import TypedDict, List, Dict, Any


class BrowserState(TypedDict):
    goal: str
    start_url: str
    title: str

    # 📄 raw page (browser output)
    page_content: List[Dict[str, Any]]

    # 🧩 chunked DOM
    chunks: List[Dict[str, Any]]

    # 🔢 embeddings
    vector_db: Any

    # 🔍 RAG retrieval output (NEW)
    retrieved_context: List[str]

    # 🧠 query used for retrieval (NEW - optional but useful)
    search_query: str

    # 🧠 planner output (final AI decision)
    plan: str

    # 👀 optional evaluation step
    review: str
    result: str