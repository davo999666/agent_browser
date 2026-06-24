from typing import Dict, Any
import json


from chains.planner_chain import planner_chain, query_chain
from tools.retriever import retrieve


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    goal = state.get("goal", "")
    vector_db = state.get("vector_db")  # 👈 your FAISS/Chroma DB

    # 🧠 1. LLM decides what to search (simple heuristic or prompt)
    search_query = query_chain.invoke({
        "goal": goal
    })

    # 🔍 2. retrieve relevant page data from vector DB
    retrieved_chunks = retrieve(search_query, vector_db)

    # 📄 3. build context from retrieval
    context = "\n".join(retrieved_chunks)

    # 🧠 4. LLM makes final plan using retrieved info
    result = planner_chain.invoke({
        "goal": goal,
        "page_data": context[:4000]
    })

    return {
        **state,
        "retrieved_context": retrieved_chunks,
        "plan": result
    }