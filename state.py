from typing import TypedDict, List, Dict, Any, Optional


class BrowserState(TypedDict, total=False):
    goal: str
    start_url: str

    # 📄 page output from browser
    title: Optional[str]
    url: Optional[str]
    page_content: List[Dict[str, Any]]

    # 🧩 chunked DOM
    chunks: List[Dict[str, Any]]

    # 🔢 vector store
    vector_db: Any

    # 🔍 retrieval results (structured!)
    retrieved_context: List[Dict[str, Any]]

    # 🧠 search query
    search_query: Optional[str]

    # 🧠 planner output (IMPORTANT: dict, not string)
    plan: Dict[str, Any]

    # 👀 optional evaluation
    review: Optional[str]

    # 🎯 final result
    result: Optional[Any]

    # 🌐 runtime browser object (IMPORTANT)
    browser: Any

    # 📄 current page object (optional but useful)
    page: Any