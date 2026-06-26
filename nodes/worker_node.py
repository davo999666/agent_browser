"""Agentic worker node: executes ONE action per invocation."""

import json
import logging
from collections import Counter

from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

from chains.worker_chain import TOOL_MAP, worker_llm_with_tools
from prompts.worker_prompt import worker_prompt
from tools.browser_tools import _get_page

logger = logging.getLogger(__name__)

# Maximum number of consecutive identical actions before forcing a stop
MAX_REPEATED_ACTIONS = 3


def _execute_tool_call(tool_call: dict) -> ToolMessage:
    """Execute a single LangChain tool_call dict and return a ToolMessage."""
    name = tool_call["name"]
    args = tool_call["args"]
    call_id = tool_call["id"]

    tool_fn = TOOL_MAP.get(name)
    if tool_fn is None:
        result = f"Error: unknown tool '{name}'"
    else:
        try:
            result = tool_fn.invoke(args)
        except Exception as e:
            result = f"Error executing '{name}': {str(e)}"

    return ToolMessage(content=str(result), tool_call_id=call_id)


def _get_current_url() -> str:
    """Safely get the current page URL."""
    try:
        page = _get_page()
        return page.url
    except Exception:
        return ""


def _detect_repetition(history: list) -> bool:
    """Detect if the last N actions are identical (infinite loop)."""
    if len(history) < MAX_REPEATED_ACTIONS:
        return False

    # Get the last MAX_REPEATED_ACTIONS entries
    last_actions = history[-MAX_REPEATED_ACTIONS:]
    
    # Count occurrences of each action
    action_counts = Counter(last_actions)
    
    # If any action appears MAX_REPEATED_ACTIONS times consecutively, it's a loop
    for action, count in action_counts.items():
        if count >= MAX_REPEATED_ACTIONS:
            return True
    
    return False


def worker_node(state):
    print("============worker_node==============")
    """Execute ONE action and return.

    The worker:
    1. Invokes the LLM with current context and full message history
    2. If LLM calls a tool → execute it, record in history
    3. If LLM produces final text → task is complete
    4. Sets next_action based on:
       - "browser" if page URL changed (triggers re-extract/chunk/embed)
       - "worker" if same page (continue loop)
       - "end" if task is complete or stuck in loop

    Returns:
        - worker_history: updated history
        - worker_messages: updated full message list
        - next_action: routing decision
        - result: final answer (only if task complete)
    """
    goal = state.get("goal", "")
    plan = state.get("plan", {})
    plan_text = str(plan)
    history = list(state.get("worker_history", []))
    messages = list(state.get("worker_messages", []))
    url_before = state.get("url", "") or _get_current_url()

    # Check for infinite loop before proceeding
    if _detect_repetition(history):
        print(f"⚠️ Detected infinite loop! Last {MAX_REPEATED_ACTIONS} actions were identical. Forcing completion.")
        final_text = "Task incomplete: Agent detected an infinite loop and was forced to stop. Please review the goal and plan."
        history.append(f"[FINAL - LOOP DETECTED] {final_text}")
        
        return {
            "result": final_text,
            "worker_history": history,
            "worker_messages": messages,
            "next_action": "end",
        }

    # Build initial prompt if this is the first invocation
    if not messages:
        history_text = "\n".join(history) if history else "(no actions yet)"
        prompt_messages = worker_prompt.invoke({
            "goal": goal,
            "plan": plan_text,
            "history": history_text,
        }).to_messages()
        messages = list(prompt_messages)

    # Invoke LLM with full message history
    print(f"\n🔄 Worker deciding next action...")
    response = worker_llm_with_tools.invoke(messages)

    # Add the AI response to message history
    messages.append(response)

    # Check if the LLM wants to call tools
    tool_calls = getattr(response, "tool_calls", None) or []

    if not tool_calls:
        # LLM produced a final text answer — task is complete
        final_text = response.content if hasattr(response, "content") else str(response)
        print(f"✅ Worker complete: {final_text[:300]}")
        history.append(f"[FINAL] {final_text}")

        return {
            "result": final_text,
            "worker_history": history,
            "worker_messages": messages,
            "next_action": "end",
        }

    # Execute the first tool call only (one action per invocation)
    tc = tool_calls[0]
    tool_name = tc["name"]
    print(f"  🔧 Calling {tool_name}({tc['args']})")

    tool_msg = _execute_tool_call(tc)
    print(f"     → {tool_msg.content[:200]}")

    # Add tool message to conversation history
    messages.append(tool_msg)

    # Record in human-readable history (with increased truncation limit)
    history.append(f"{tool_name}({tc['args']}) → {tool_msg.content[:500]}")

    # Check if this browser action caused a page navigation
    next_action = "worker"  # default: continue on same page

    if tool_name in ("navigate_tool", "click_tool", "go_back_tool", "press_key_tool"):
        url_after = _get_current_url()
        if url_after and url_after != url_before:
            print(f"  📄 Page changed: {url_before} → {url_after}")
            next_action = "browser"  # trigger re-extract/chunk/embed

    return {
        "worker_history": history,
        "worker_messages": messages,
        "next_action": next_action,
    }
