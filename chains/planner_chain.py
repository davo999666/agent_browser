from langchain_core.output_parsers import StrOutputParser
from llm.model import model

from prompts.planner_prompt import planner_prompt, query_prompt
from prompts.final_prompt import final_prompt  # 👈 add this

parser = StrOutputParser()

# 🧠 1. Query generation chain (RAG search query)
query_chain = query_prompt | model | parser

# 🧠 2. Planner chain (final reasoning plan)
planner_chain = planner_prompt | model | parser

# 🧠 3. Final answer chain (clean user output)
final_chain = final_prompt | model | parser