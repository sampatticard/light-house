# Sampatti LLM API & Form Filler

A modular, scalable FastAPI server for local LLM-powered form filling, browser automation, and chat, supporting both Ollama and MCP backends. Designed for decentralized, privacy-first document and form workflows as described in the Sampatti Card/Lighthouse architecture.

---

## Features
- **Modular LLM backend**: Easily switch between Ollama (local SLM) and MCP (e.g., llama.cpp) for prompt-based inference.
- **Automated form filling**: Extracts fields from uploaded documents (PDFs/images) using LLMs, matches with user data, and can auto-fill web forms via browser automation.
- **Browser agent integration**: Generates and executes browser actions (navigate, click, type, extract, etc.) using LLM-generated plans.
- **Clean, async API endpoints**: For chat, form extraction, and browser automation workflows.
- **Extensible and testable**: Add new LLMs, form logic, or browser actions with minimal changes.

---

## High-Level Architecture

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  Lighthouse   │ ←→   │  Harborlink   │ ←→   │ Bank Connect. │
│ (user device) │      │ (cloud core)  │      │ (per-bank)    │
└───────────────┘      └───────────────┘      └───────────────┘
      │                        │                        │
      │ 1️⃣ chat / browseruse  │                        │
      ▼                        │                        │
 [Local SLM (Ollama)]          │                        │
      │                        ▼                        │
 [Local docs + OCR]      [Policy/Offer Engine]          │
      │                        │                        ▼
 [ZK proof gen]   ──encrypted docs/claims──▶  [Data Mesh]
```

---

## Codebase Structure

- `llm/` — LLM client abstractions and implementations
  - `llm_client.py`: Abstract base for LLMs
  - `ollama_client.py`, `mcp_client.py`: Implementations for Ollama and MCP
  - `llm_factory.py`: Returns the correct LLM client
- `formfiller/` — Form filling, parsing, and field matching logic
  - `form_filler.py`: Orchestrates extraction, matching, and LLM calls
  - `form_parser.py`: Extracts text from uploads (PDF/image)
  - `field_matcher.py`: Fuzzy field matching
- `browseragent/` — Browser automation DSL and execution
  - Each action class (Navigate, Click, Type, Wait, Extract) in its own file
  - `core.py`: Generates actions from LLM, runs them via Playwright
- `formdiscovery/` — Form discovery logic
  - `form_discovery_result.py`, `discovery.py`: Typed result and main function
- `app/main.py` — FastAPI endpoints for all workflows
- `tests/` — Pytest-based tests for LLM, form filling, and browser agent

---

## API Endpoints

### `/llm_chat`
- **POST** `{ "prompt": "...", "model": "phi3:mini" }`
- Returns: `{ "response": "..." }`
- Uses Ollama by default (can extend for MCP)

### `/fill_form`
- **POST** form-data: `form_type`, `llm` ("ollama" or "mcp"), `prompt`, `user_data`, `autofill` (bool), `form_url`, and a file upload
- Returns: matched fields, missing fields, LLM-extracted data, and (if `autofill` is true) browser automation results
- **Workflow:**
  1. Extracts text from the uploaded document
  2. Uses LLM to extract field values
  3. Matches with user data
  4. (Optional) Uses browser agent to fill the form at `form_url` using generated actions

### `/discover`, `/extract_fields`, `/parse/{form_type}`, `/match_fields`, `/autofill`
- Additional endpoints for form discovery, field extraction, parsing, matching, and direct browser automation.

---

## Example Usage

### Fill a Form and Autofill in Browser
```bash
curl -X POST "http://localhost:8000/fill_form" \
  -F form_type=loan_application \
  -F llm=ollama \
  -F prompt="Extract all fields for the loan application" \
  -F user_data='{"name": "Alice"}' \
  -F autofill=true \
  -F form_url="https://bank.com/loan-form" \
  -F file=@/path/to/document.pdf
```

### LLM Chat
```bash
curl -X POST "http://localhost:8000/llm_chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is a home loan?", "model": "phi3:mini"}'
```

---

## Extending the Codebase
- **Add a new LLM**: Implement `LLMClient` and register in `llm_factory.py`.
- **Add a new browser action**: Create a new class in `browseragent/` and update the union.
- **Add new form logic**: Extend `formfiller/` with new parsing or matching strategies.

---

## Testing
Run all tests with:
```bash
pytest
```

---

## License
MIT
