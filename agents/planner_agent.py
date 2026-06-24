from typing import Dict, Any


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Planner Agent:
    Creates a simple step-by-step plan based on the goal.
    """

    goal = state.get("goal", "")

    # Simple planning logic (you can later replace with LLM)
    plan = []

    return {
        "plan": "\n".join(plan)
    }