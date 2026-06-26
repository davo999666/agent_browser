from typing import Dict, Any

def chunk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("===============chunk_node=================")
    page = state.get("page_content", {})
    nodes = page.get("data", [])

    chunks = []
    keys = ["tag", "class", "href", "text", "title", "role", "placeholder", "onClick"]

    for node in nodes:
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