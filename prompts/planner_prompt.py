from langchain_core.prompts import ChatPromptTemplate

# 🧠 Planner prompt
planner_prompt = ChatPromptTemplate.from_template("""
You are an AI browser planner.

GOAL:
{goal}

PAGE DATA:
{page_data}

TASK:
1. Understand what is on the page
2. Decide what is relevant to the goal
3. Create a step-by-step plan
4. Return ONLY JSON:

{{
  "strategy": "string",
  "focus": "string",
  "next_actions": ["step1", "step2"]
}}
""")

# 🔍 Query generator prompt
query_prompt = ChatPromptTemplate.from_template("""
You are a data filtering planner for a web scraping agent.

GOAL:
{goal}

Step 1:
Define what VALID results look like.

Step 2:
Define what INVALID results are.

Step 3:
List keywords that represent HIGH-RELEVANCE data only.

Return ONLY structured output:
- valid_data:
- invalid_data:
- search_terms:
""")