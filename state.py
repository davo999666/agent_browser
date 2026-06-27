from typing import TypedDict, List, Dict, Any, Optional


class BrowserState(TypedDict, total=False):
    goal: str
    start_url: str

    url: Optional[str]

    page_content: Dict[str, Any]

    chunks: List[Dict[str, Any]]

    plan: Dict[str, Any]

    worker_history: List[str]
    worker_messages: List[Any]  # Full LangChain message objects for LLM conversation

    next_action: str
