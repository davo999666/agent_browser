import json
from typing import Dict, Any
from vector_store.faiss_db import get_vector_db
from tools.retriever import retrieve
from chains.planner_chain import planner_chain, query_chain


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("==============planner_node================")
    goal = state.get("goal", "")
    vector_db = get_vector_db()
    # ----------------------------
    # 1. Get queries (JSON safe)
    # ----------------------------
    search_query = query_chain.invoke({"goal": goal})

    search_query = [q.strip() for q in search_query if isinstance(q, str) and q.strip()]
    
    k = 3 if len(search_query) > 5 else 6

    # ----------------------------
    # 2. multi retrieval (FIXED)
    # ----------------------------
    retrieved_chunks = []
    for query in search_query:
        chunks = retrieve(query, vector_db, k=k)
        retrieved_chunks.extend(chunks)
    # ----------------------------
    # 3. build context 
    # ----------------------------
    context = "\n\n".join(
        f"TEXT: {c.get('text')}\n"
        f"metadata: {c.get('metadata')}\n"
        for c in retrieved_chunks
    )
    # ----------------------------
    # 4. planner
    # ----------------------------
    result = planner_chain.invoke({
        "goal": goal,
        "page_data": context
    })

    # ----------------------------
    # 5. logs (SAFE)
    # ----------------------------
    with open("output/search_query_for_plan.txt", "w", encoding="utf-8") as f:
        f.write(str(search_query))

    with open("output/retrieved_context.json", "w", encoding="utf-8") as f:
        json.dump(retrieved_chunks, f, ensure_ascii=False, indent=2)

    with open("output/plan.txt", "w", encoding="utf-8") as f:
        f.write(str(result))

    return {
        "search_query": search_query,
        "retrieved_context": retrieved_chunks,
        "plan": result
    }