from typing import Dict, Any, List

def chunk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    page = state.get("page_content", [])

    chunks = []

    keys = ["tag", "class", "href", "text", "title", "role", "placeholder", "onClick"]

    for node in page:
        if not isinstance(node, dict):
            continue

        clean_node = {
            k: node.get(k)
            for k in keys
            if node.get(k)
        }

        chunks.append(clean_node)

    return {
        **state,
        "chunks": chunks
    }