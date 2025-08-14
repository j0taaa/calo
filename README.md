## GPT-5 Agent with PDF RAG + Web Search

This project wires up:
- PDF retrieval over the provided HCIP Cloud Service Solutions Architect PDF
- Web search (DuckDuckGo by default; Bing/Tavily optional)
- OpenAI API with high reasoning effort
- A CLI to run quick tests

### Setup
1. Create a virtualenv and install deps:
```bash
python -m venv /workspace/.venv && source /workspace/.venv/bin/activate
pip install -r /workspace/requirements.txt
```
2. Configure environment variables:
```bash
cp /workspace/.env.example /workspace/.env
# edit /workspace/.env to add OPENAI_API_KEY (and optional search keys)
# optional: adjust OPENAI_TOOL_LOOP_LIMIT to allow more tool calls (default 6)
```

### Index the PDF
```bash
python /workspace/main.py setup-pdf
```

### Ask a question (uses tools automatically)
```bash
python /workspace/main.py ask --q "Summarize the core services discussed in the HCIP architect training material."
```

### Run quick tests
```bash
python /workspace/main.py test
```

Data is stored under `data/` in the project root.
