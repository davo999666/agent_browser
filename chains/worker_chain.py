from llm.model import model
from prompts.worker_prompt import worker_prompt
from tools.browser_tools import ALL_BROWSER_TOOLS

# For lookup by name
TOOL_MAP = {t.name: t for t in ALL_BROWSER_TOOLS}

# For OpenAI tool calling
worker_llm_with_tools = model.bind_tools(ALL_BROWSER_TOOLS)

worker_chain = worker_prompt | worker_llm_with_tools