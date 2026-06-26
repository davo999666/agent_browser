from state import BrowserState


def worker_router(state: BrowserState):
    """Route after worker executes one action.

    Returns:
        - "browser": page URL changed → re-extract/chunk/embed
        - "worker": same page → continue worker loop
        - "end": task is complete
    """
    return state.get("next_action", "end")


def browser_router(state: BrowserState):
    """Route after browser extracts page content.

    Always routes to chunker to process the new page content.
    """
    return "chunker"


def embedder_router(state: BrowserState):
    """Route after embedding page content.

    Returns:
        - "planner": no plan exists yet (initial run)
        - "worker": plan already exists (subsequent page loads)
    """
    plan = state.get("plan")
    if plan:
        return "worker"
    return "planner"
