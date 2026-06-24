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

IMPORTANT RULES:
- Use ONLY information from PAGE DATA
- Do NOT hallucinate elements
- Steps must be in correct order
- Create as many steps as needed (minimum 1, maximum 10)

OUTPUT FORMAT:

{{
  "steps": [
    {{
      "id": 1,
      "element": "description",
      "action": "click | type | search | navigate",
      "input": "text or null",
      "reason": "why this step is needed"
    }},
    {{
      "id": 2,
      "element": "description",
      "action": "click | type | search | navigate",
      "input": "text or null",
      "reason": "why this step is needed"
    }}
  ]
}}
""")

# 🔍 Query generator prompt
query_prompt = ChatPromptTemplate.from_template("""
Analyze the goal and identify only the types of pages, page elements, and page data needed to accomplish it.

Return a short query containing only relevant page types and UI elements.

Examples:

Goal: Create an account
Query: registration page, signup form, email input, password input, submit button

Goal: Find contact information
Query: contact page, help page, phone number, email address, contact form

Goal: Search for a product
Query: search page, search input, category page, product page, filter menu

Goal: Apply for a job
Query: careers page, job listings, job details, apply button, application form, resume upload, submit button

Do NOT repeat the goal.
Do NOT describe the task.
Do NOT explain your reasoning.

GOAL:
{goal}

Return ONLY the short query.
""")
