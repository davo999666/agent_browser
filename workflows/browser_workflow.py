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

        graph.add_node("browser", browser_node)
        graph.add_node("chunker", chunk_node)
        graph.add_node("embedder", embed_node)
        graph.add_node("planner", planner_node)
        graph.add_node("closer", close_browser)

        graph.set_entry_point("browser")

        graph.add_edge("browser", "chunker")
        graph.add_edge("chunker", "embedder")
        graph.add_edge("embedder", "planner")
        graph.add_edge("planner", "closer")
        graph.add_edge("closer", END)


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
        page = result.get("page_content", {})
        data = page.get("data", [])
        chunks = result.get("chunks", [])
        vector_db = result.get("vector_db")    
        retrieved = result.get("retrieved_context", [])
        search_query = result.get("search_query", "")
        plan = result.get("plan", "")

        # ---------------- OUTPUT JSON ----------------
        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # ---------------- CHUNKS ----------------
        with open("chunks.txt", "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                f.write(f"\n--- CHUNK {i+1} ---\n")
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        # ---------------- EMBEDDINGS ----------------
        with open("embeddings.txt", "w", encoding="utf-8") as f:
        # index_to_docstore_id maps FAISS internal int index -> docstore id
            for i, docstore_id in vector_db.index_to_docstore_id.items():
                doc = vector_db.docstore.search(docstore_id)
                vector = vector_db.index.reconstruct(i)  # numpy array, shape (dim,)
                f.write(f"\n--- EMBEDDING {i+1} ---\n")
                f.write("META:\n")
                f.write(json.dumps(doc.metadata, ensure_ascii=False, indent=2) + "\n\n")
                f.write("TEXT:\n")
                f.write(doc.page_content + "\n\n")
                f.write("VECTOR (first 10 dims):\n")
                f.write(str(vector[:10].tolist()) + "\n")
                f.write(f"VECTOR DIM: {len(vector)}\n")

        
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