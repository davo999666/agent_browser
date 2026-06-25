from llm.model import model
from prompts.worker_prompt import worker_prompt
from tools.browser_tools import ALL_BROWSER_TOOLS

# Bind all browser tools to the LLM for tool-calling
worker_llm_with_tools = model.bind_tools(ALL_BROWSER_TOOLS)

# Worker chain: prompt -> LLM with tools
# Input variables: task, current_step, history
worker_chain = worker_prompt | worker_llm_with_tools
