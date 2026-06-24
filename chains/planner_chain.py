from langchain_core.output_parsers import StrOutputParser
from llm.model import model

from prompts.planner_prompt import planner_prompt, query_prompt

parser = StrOutputParser()

# 🧠 1. Query generation chain (RAG search query)
query_chain = query_prompt | model | parser

# 🧠 2. Planner chain (final reasoning)
planner_chain = planner_prompt | model | parser