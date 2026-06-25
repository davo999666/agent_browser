import json
import logging

from langchain_core.messages import ToolMessage

from chains.worker_chain import TOOL_MAP, worker_llm_with_tools
from llm.model import model
from prompts.worker_prompt import worker_prompt
from tools.browser_lifecycle import BrowserLifecycle
from tools.browser_tools import set_browser_lifecycle

logger = logging.getLogger(__name__)

# Maximum tool-call iterations per step to prevent infinite loops
MAX_ITERATIONS_PER_STEP = 20


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


def worker_node(state):
    """Execute plan steps using browser tools until the task is completed."""
    browser_lifecycle: BrowserLifecycle = state.get("browser_lifecycle")
    # Wire up BrowserLifecycle so browser_tools can access the page
    set_browser_lifecycle(browser_lifecycle)
    # ------------------------------------------------------------------
    # Parse plan
    # ------------------------------------------------------------------
    plan = state.get("plan", {})
    plan_text = str(plan)
    try:
        plan_dict = json.loads(plan_text)
    except (json.JSONDecodeError, TypeError):
        plan_dict = plan if isinstance(plan, dict) else {}

    steps = plan_dict.get("steps", [])
    goal = state.get("goal", "")
    # ------------------------------------------------------------------
    # Execute each step
    # ------------------------------------------------------------------
    history: list[str] = []  # running log of completed actions
    step_results: list[dict] = []

    for step in steps:
        step_id = step.get("id", "?")
        step_summary = (
            f"Step {step_id}: action={step.get('action')}, "
            f"element={step.get('element')}, input={step.get('input')}, "
            f"reason={step.get('reason')}"
        )
        print(f"▶ EXECUTING {step_summary}")
        
        history_text = "\n".join(history) if history else "(no actions yet)"

        # ---- Tool-call loop for this step ----
        # Build the initial message list from the prompt template so that
        # system + human messages persist across tool-call rounds.
        prompt_messages = worker_prompt.invoke({
            "task": goal,
            "current_step": step_summary,
            "history": history_text,
        }).to_messages()

        messages = list(prompt_messages)  # mutable copy

        for iteration in range(1, MAX_ITERATIONS_PER_STEP + 1):
            # Invoke LLM with full message history (including tools)
            response = worker_llm_with_tools.invoke(messages)

            # Check if the LLM wants to call tools
            tool_calls = getattr(response, "tool_calls", None) or []

            if not tool_calls:
                # LLM produced a final text answer for this step
                final_text = response.content if hasattr(response, "content") else str(response)
                print(f"  ✅ Step {step_id} complete: {final_text[:200]}")
                history.append(f"[Step {step_id}] {final_text}")
                step_results.append({"step_id": step_id, "result": final_text})
                break

            # Append AI response with tool_calls, then execute each tool
            messages.append(response)

            for tc in tool_calls:
                print(f"  🔧 Calling {tc['name']}({tc['args']})")
                tool_msg = _execute_tool_call(tc)
                print(f"     → {tool_msg.content[:200]}")
                messages.append(tool_msg)
                history.append(
                    f"[Step {step_id}] {tc['name']}({tc['args']}) → {tool_msg.content[:150]}"
                )
        else:
            # Hit iteration limit
            warning = f"Step {step_id} hit max iterations ({MAX_ITERATIONS_PER_STEP})"
            print(f"  ⚠️  {warning}")
            history.append(f"[Step {step_id}] {warning}")
            step_results.append({"step_id": step_id, "result": warning})

    # ------------------------------------------------------------------
    # Build final result summary
    # ------------------------------------------------------------------
    result_summary = "\n".join(
        f"Step {r['step_id']}: {r['result']}" for r in step_results
    )
    print(f"\n🏁 WORKER FINISHED — {len(step_results)} steps executed")

    return {
        **state,
        "worker_history": history,
        "result": result_summary,
    }