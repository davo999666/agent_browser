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

                            {
                            "strategy": "...",
                            "focus": "...",
                            "next_actions": ["..."]
                            }
""")

# 🔍 Query generator prompt (FIXED)
query_prompt = ChatPromptTemplate.from_template("""
                    
                    From this goal, create a search query for retrieving relevant web page data.

                    GOAL:
                    {goal}

                    Return ONLY the search query.
                                                
   """)