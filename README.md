# Agent Browser

An AI-powered browser automation agent built with LangGraph that can navigate websites, extract information, and execute multi-step tasks autonomously.

## Features

- **Autonomous Web Navigation**: Automatically browse websites to find specific information
- **Multi-Agent Workflow**: Uses a stateful graph-based architecture with specialized nodes for different tasks
- **Vector Search Integration**: Leverages FAISS for semantic search and context retrieval
- **LLM-Powered Planning**: Generates execution plans based on user goals using advanced language models

## Architecture

The agent follows this workflow:

```
Browser → Chunker → Embedder → Planner → Worker
```

### Components

| Component | Responsibility |
|-----------|---------------|
| `browser_node` | Navigates to URLs and extracts page content |
| `chunk_node` | Splits extracted text into manageable chunks |
| `embedder_node` | Creates vector embeddings for semantic search |
| `planner_node` | Generates a plan to achieve the user's goal |
| `worker_node` | Executes tasks based on the generated plan |

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent_browser
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the agent with a goal and starting URL:

```python
from playwright.sync_api import sync_playwright
from workflows.browser_workflow import BrowserWorkflow

p = sync_playwright().start()
browser = p.chromium.launch(headless=False)

goal = "Find an apartment for sale with a budget of $50,000."
start_url = "https://www.list.am/en/"

agent = BrowserWorkflow()
agent.run(goal, start_url, browser)

browser.close()
p.stop()
```

## Output Files

After running the agent, the following files will be generated:

| File | Description |
|------|-------------|
| `output.json` | Extracted data from pages visited |
| `chunks.txt` | Text chunks processed by the chunker node |
| `embeddings.txt` | Vector embeddings with metadata and text content |
| `retrieved_context.json` | Context retrieved via vector search |
| `search_query.txt` | The final search query generated |
| `plan.txt` | The execution plan generated for the goal |

## Project Structure

```
agent_browser/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── state.py               # State management for LangGraph
├── agents/                # Agent definitions
│   └── planner_agent.py
├── chains/                # Custom chains
│   └── planner_chain.py
├── llm/                   # LLM configuration
│   └── model.py
├── nodes/                 # Graph nodes
│   ├── browser_extractor_node.py
│   ├── chunk_node.py
│   ├── embedding_nodes.py
│   ├── planner_node.py
│   └── worker_node.py
├── prompts/               # Prompt templates
│   └── planner_prompt.py
├── tools/                 # Custom tools
│   └── retriever.py
├── vector_store/          # Vector database integration
│   └── faiss_db.py
├── workflows/             # Workflow definitions
│   └── browser_workflow.py
└── README.md              # This file
```

## Dependencies

- `langgraph` - Stateful multi-agent orchestration framework
- `playwright` - Browser automation library
- `langchain-text-splitters` - Text chunking utilities
- `langchain_openai` - OpenAI language model integration
- `langchain-huggingface` - Hugging Face model integration
- `faiss-cpu` - Facebook AI Similarity Search for vector operations
- `sentence_transformers` - Pre-trained sentence transformers for embeddings

## License

MIT License
