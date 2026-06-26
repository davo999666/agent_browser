import json

from langgraph.graph import StateGraph, END


from vector_store.faiss_db import create_vector_db, get_vector_db

from state import BrowserState

from nodes.browser_extractor_node import browser_node
from nodes.chunk_node import chunk_node
from nodes.embedding_nodes import embed_node
from nodes.planner_node import planner_node
from nodes.worker_node import worker_node
from workflows.routers import worker_router, browser_router, embedder_router


class BrowserWorkflow:
    """Browser automation workflow with agentic worker.

    Architecture:
    1. Initial: browser → chunker → embedder → planner → worker
    2. Worker loop:
       - If page changed: worker → browser → chunker → embedder → worker (skip planner)
       - If same page: worker → worker (continue loop)
       - If task complete: worker → END

    The worker executes ONE action per invocation, then the graph routes
    based on whether a new page was detected.
    """

    def __init__(self):
        self.vector_db = create_vector_db()

        graph = StateGraph(BrowserState)

        graph.add_node("browser", browser_node)
        graph.add_node("chunker", chunk_node)
        graph.add_node("embedder", embed_node)
        graph.add_node("planner", planner_node)
        graph.add_node("worker", worker_node)

        graph.set_entry_point("browser")

        graph.add_edge("browser", "chunker")
        graph.add_edge("chunker", "embedder") 
        # embedder → planner OR worker (skip planner if plan exists)
        graph.add_conditional_edges(
            "embedder",
            embedder_router,
            {
                "planner": "planner",  # initial run: create plan
                "worker": "worker",    # subsequent pages: skip planner
            },
        )
        graph.add_edge("planner", "worker")
        # Worker routing: decides next step based on action result
        graph.add_conditional_edges(
            "worker",
            worker_router,
            {
                "browser": "browser",  # page changed → re-extract/chunk/embed
                "worker": "worker",    # same page → continue loop
                "end": END,            # task complete
            },
        )

        self.app = graph.compile()

    def run(self, goal: str, start_url: str):

        result = self.app.invoke(
            {
                "goal": goal,
                "start_url": start_url,
                "page_content": {},
            }
        )
        page = result.get("page_content", {})
        data = page.get("data", [])
        chunks = result.get("chunks", [])
        vector_db = get_vector_db()
        retrieved = result.get("retrieved_context", [])
        search_query = result.get("search_query", "")
        plan = result.get("plan", "")
        worker_history = result.get("worker_history", [])
        final_result = result.get("result", "")

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
        with open("retrieved_context.json", "w", encoding="utf-8") as f:
            json.dump(retrieved, f, ensure_ascii=False, indent=2)

        # ---------------- QUERY ----------------
        with open("search_query.txt", "w", encoding="utf-8") as f:
            f.write(search_query)

        # ---------------- PLAN ----------------
        with open("plan.txt", "w", encoding="utf-8") as f:
            f.write(str(plan))

        # ---------------- WORKER HISTORY ----------------
        with open("worker_history.txt", "w", encoding="utf-8") as f:
            for entry in worker_history:
                f.write(entry + "\n")

        # ---------------- FINAL RESULT ----------------
        with open("final_result.txt", "w", encoding="utf-8") as f:
            f.write(str(final_result))

        return result
