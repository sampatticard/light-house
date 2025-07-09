# Sampatti LLM API & Form Filler

A modular, scalable FastAPI server for local LLM-powered form filling and chat, supporting both Ollama and MCP backends.

## Features
- Modular LLM backend (Ollama, MCP, easily extensible)
- Automated form filling from uploaded documents using LLM extraction
- Clean, async API endpoints for chat and form workflows
- Easily extensible and testable codebase

## Requirements
- Python 3.8+
- Ollama (https://ollama.com) for local LLM
- (Optional) MCP/llama.cpp for mobile-compatible LLM
- All dependencies in `requirements.txt`

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the API server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Pull a model for Ollama (if using):
   ```bash
   ollama pull phi3:mini
   ```

## API Endpoints

### `/llm_chat`
- POST `{ "prompt": "...", "model": "phi3:mini" }`
- Returns: `{ "response": "..." }`
- Uses Ollama by default (can extend for MCP)

### `/fill_form`
- POST form-data: `form_type`, `llm` ("ollama" or "mcp"), `prompt`, `user_data`, and a file upload
- Returns: matched fields, missing fields, and LLM-extracted data

## Project Structure
- `llm/` — LLM client abstractions and implementations
- `formfiller/` — Form filling, parsing, and field matching logic
- `app/main.py` — FastAPI endpoints
- `tests/` — Pytest-based tests for LLM and form filling

## Testing
Run all tests with:
```bash
pytest
```

## Extending
- Add new LLM backends by implementing `LLMClient` and registering in `llm_factory.py`.
- Add new form logic in `formfiller/`.

## License
MIT
