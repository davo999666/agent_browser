from langchain_core.prompts import ChatPromptTemplate

# 🧠 Planner prompt
planner_prompt = ChatPromptTemplate.from_template("""
You are an AI browser planner.

GOAL:
{goal}

PAGE DATA:
{page_data}

TASK:
1. Understand the page structure and available interactive elements
2. Create a step-by-step plan to achieve the goal
3. Each step must map to real elements in PAGE DATA

IMPORTANT RULES:
- Use ONLY information from PAGE DATA
- Do NOT hallucinate elements
- Steps must be in correct order
- Create steps required to complete the task; the number of steps is not fixed and should depend on the complexity of the goal.


OUTPUT FORMAT (STRICT JSON):

{{
  "steps": [
    {{
      "id": 1,
      "target": "element description from page data",
      "action": "click | type | search | navigate | scroll | wait | go_back",
      "input": "text or null",
      "reason": "why this step is needed"
    }},
    {{
      "id": 2,
      "target": "element description from page data",
      "action": "click | type | search | navigate | scroll | wait | go_back",
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
Query: [contact page, help page, phone number, email address, contact form]

Goal: Search for a product
Query: [search page, search input, category page, product page, filter menu]

Goal: Apply for a job
Query: [careers page, job listings, job details, apply button, application form, resume upload, submit button]

Do NOT repeat the goal.
Do NOT describe the task.
Do NOT explain your reasoning.

GOAL:
{goal}
                                                
IMPORTANT RULES:
- Return ONLY valid JSON array of strings

Return ONLY the short query.
""")
