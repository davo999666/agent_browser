import json
from typing import Dict, Any

from chains.planner_chain import planner_chain, query_chain
from tools.retriever import retrieve
from vector_store.faiss_db import get_vector_db


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("==============planner_node================")
    goal = state.get("goal", "")
    vector_db = get_vector_db()

    # 🧠 1. LLM decides what to search (simple heuristic or prompt)
    search_query = query_chain.invoke({
        "goal": goal
    })

    # 🔍 2. retrieve relevant page data from vector DB
    retrieved_chunks = retrieve(search_query, vector_db, k=20)

    # 📄 3. build context from retrieval
    context = json.dumps(retrieved_chunks, ensure_ascii=False, indent=2)

    # 🧠 4. LLM makes final plan using retrieved info
    result = planner_chain.invoke({
        "goal": goal,
        "page_data": context[:4000]
    })

    return {
        **state,
        "search_query" : search_query,
        "retrieved_context": retrieved_chunks,
        "plan": result
    }