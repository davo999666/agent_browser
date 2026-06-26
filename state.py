from typing import TypedDict, List, Dict, Any, Optional


class BrowserState(TypedDict, total=False):
    goal: str
    start_url: str

    # title: Optional[str]
    url: Optional[str]
    # previous_url: Optional[str]
    page_content: Dict[str, Any]

    chunks: List[Dict[str, Any]]

    # retrieved_context: List[Dict[str, Any]]

    # search_query: Optional[str]
    # memory_query: Optional[str]
    # memory_results: List[Dict[str, Any]]

    plan: Dict[str, Any]

    worker_history: List[str]
    worker_messages: List[Any]  # Full LangChain message objects for LLM conversation

    # result: Optional[Any]
    next_action: str
