# Agent Browser - MVP Documentation

## Overview

Agent Browser is an AI-powered browser automation agent built with LangGraph that can navigate websites, extract information, and execute multi-step tasks autonomously.

## Core Features (MVP)

### 1. Autonomous Web Navigation
- Navigate to specified URLs using Playwright
- Extract page content including text, links, and structured data
- Handle multiple pages in a browsing session

### 2. Multi-Agent Workflow
- **Browser Node**: Handles web navigation and content extraction
- **Chunker Node**: Splits extracted text into manageable chunks for processing
- **Embedder Node**: Creates vector embeddings for semantic search capabilities
- **Planner Node**: Generates execution plans based on user goals using LLMs
- **Worker Node**: Executes tasks according to the generated plan

### 3. Vector Search Integration
- FAISS-based vector database for efficient similarity search
- Context retrieval from processed web content
- Semantic matching of queries against extracted information

### 4. LLM-Powered Planning
- Goal-oriented task planning using advanced language models
- Dynamic plan generation based on available context
- Iterative refinement of execution strategies

## Architecture

```
Browser → Chunker → Embedder → Planner → Worker
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `browser_node` | Navigates to URLs and extracts page content |
| `chunk_node` | Splits extracted text into manageable chunks |
| `embedder_node` | Creates vector embeddings for semantic search |
| `planner_node` | Generates a plan to achieve the user's goal |
| `worker_node` | Executes tasks based on the generated plan |

## Key Files Structure

```
agent_browser/
├── main.py                 # Entry point - orchestrates workflow execution
├── state.py               # State management for LangGraph workflow
├── nodes/
│   ├── browser_extractor_node.py  # Browser navigation and extraction
│   ├── chunk_node.py              # Text splitting logic
│   ├── embedding_nodes.py         # Vector embedding generation
│   ├── planner_node.py            # Plan generation from goals
│   └── worker_node.py             # Task execution based on plans
├── prompts/
│   ├── planner_prompt.py          # LLM prompt templates for planning
│   └── worker_prompt.py           # LLM prompt templates for workers
├── tools/
│   ├── browser_lifecycle.py       # Browser session management
│   ├── browser_tools.py           # Browser automation utilities
│   └── retriever.py               # Vector search retrieval logic
├── vector_store/
│   └── faiss_db.py                # FAISS database integration
├── workflows/
│   ├── browser_workflow.py        # Main workflow orchestration
│   └── routers.py                 # Workflow routing logic
└── chains/
    ├── planner_chain.py           # Planner-specific chain logic
    └── worker_chain.py            # Worker-specific chain logic
```

## Output Files Generated

| File | Description |
|------|-------------|
| `output.json` | Extracted data from pages visited |
| `chunks.txt` | Text chunks processed by the chunker node |
| `embeddings.txt` | Vector embeddings with metadata and text content |
| `retrieved_context.json` | Context retrieved via vector search |
| `search_query.txt` | The final search query generated |
| `plan.txt` | The execution plan generated for the goal |

## Usage Example

```python
from playwright.sync_api import sync_playwright
from workflows.browser_workflow import BrowserWorkflow

p = sync_playwright().start()
browser = p.chromium.launch(headless=False)


agent = BrowserWorkflow()
agent.run(goal, start_url, browser)

browser.close()
p.stop()
```

## Dependencies (MVP)

- `langgraph` - Stateful multi-agent orchestration framework
- `playwright` - Browser automation library
- `langchain-text-splitters` - Text chunking utilities
- `langchain_openai` - OpenAI language model integration
- `langchain-huggingface` - Hugging Face model integration
- `faiss-cpu` - Facebook AI Similarity Search for vector operations
- `sentence_transformers` - Pre-trained sentence transformers for embeddings

## Installation Steps

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

## Future Enhancements (Post-MVP)

- [ ] Multi-browser support (Firefox, Safari)
- [ ] Authentication handling for protected pages
- [ ] Form filling and submission capabilities
- [ ] Image extraction and OCR integration
- [ ] Real-time progress tracking UI
- [ ] Custom tool registration system
- [ ] Parallel task execution
- [ ] Error recovery mechanisms

## License

MIT License
