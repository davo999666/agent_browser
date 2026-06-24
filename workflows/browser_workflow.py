import json

from langgraph.graph import StateGraph, END
from vector_store.faiss_db import create_vector_db



from state import BrowserState

from nodes.browser_extractor_node import browser_node, close_browser
from nodes.chunk_node import chunk_node
from nodes.embedding_nodes import embed_node
from nodes.planner_node import planner_node
# from agents.reviewer_agent import reviewer_node


class BrowserWorkflow:

    def __init__(self):
        self.vector_db = create_vector_db()

        graph = StateGraph(BrowserState)

        graph.add_node("planner", planner_node)
        graph.add_node("browser", browser_node)
        graph.add_node("chunk", chunk_node)
        graph.add_node("embed", embed_node)
        graph.add_node("close_browser", close_browser)

        graph.set_entry_point("browser")

        graph.add_edge("browser", "chunk")
        graph.add_edge("chunk", "embed")
        graph.add_edge("embed", "planner")
        graph.add_edge("planner", "close_browser")
        graph.add_edge("close_browser", END)


        self.app = graph.compile()

    def run(self, goal: str, start_url: str):

        result = self.app.invoke(
            {
                "goal": goal,
                "start_url": start_url,
                "page_content": "...",
                "vector_db": self.vector_db
            }
        )

        chunks = result.get("chunks", [])
        embeddings = result.get("embedding_nodes", [])
        retrieved = result.get("retrieved_context", [])
        search_query = result.get("search_query", "")
        plan = result.get("plan", "")

        # 🔥 REMOVE NON-JSON OBJECTS
        safe_result = dict(result)
        safe_result.pop("vector_db", None)

        # ---------------- OUTPUT JSON ----------------
        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(safe_result, f, indent=2, ensure_ascii=False)

        # ---------------- CHUNKS ----------------
        with open("chunks.txt", "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                f.write(f"\n--- CHUNK {i+1} ---\n")
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        # ---------------- EMBEDDINGS ----------------
        with open("embeddings.txt", "w", encoding="utf-8") as f:
            for i, item in enumerate(embeddings):
                f.write(f"\n--- EMBEDDING {i+1} ---\n")
                f.write(f"META: {json.dumps(item.get('metadata', {}), ensure_ascii=False)}\n")
                f.write("VECTOR (numbers):\n")
                f.write(str(item.get("vector")) + "\n")

        # ---------------- RETRIEVED ----------------
        with open("retrieved_context.txt", "w", encoding="utf-8") as f:
            for i, item in enumerate(retrieved):
                f.write(f"\n--- RETRIEVED {i+1} ---\n")
                f.write(str(item) + "\n")

        # ---------------- QUERY ----------------
        with open("search_query.txt", "w", encoding="utf-8") as f:
            f.write(search_query)

        # ---------------- PLAN ----------------
        with open("plan.txt", "w", encoding="utf-8") as f:
            f.write(str(plan))

        return result