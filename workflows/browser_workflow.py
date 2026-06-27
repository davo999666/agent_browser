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
            }
        )
   
        worker_history = result.get("worker_history", [])

        # ---------------- WORKER HISTORY ----------------
        with open("output/worker_history.txt", "w", encoding="utf-8") as f:
            for entry in worker_history:
                f.write(entry + "\n")


        return result
