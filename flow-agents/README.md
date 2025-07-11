# Modular Browser Automation Backend

This project provides a robust, modular backend for automating web form workflows (e.g., Ayushman Bharat, insurance, etc.) using Playwright (via browser-use) and LLMs (OpenAI GPT-4o).

## Features
- **Intent-driven:** User provides a natural language prompt (e.g., "Apply for Ayushman Bharat"), and the backend selects the correct workflow.
- **Multi-form support:** Easily add new forms by creating new step logic and prompt builders.
- **Modular architecture:** Clean separation of session management, agent orchestration, prompt building, error handling, and business logic.
- **Extensible:** Add new forms, workflows, or intent mappings with minimal code changes.

## Directory Structure
```
flow-agents/
  browser_toolkit/   # Core browser/session/agent logic (modular)
  services/          # Business logic (automation service)
  routes/            # Flask blueprints (API endpoints)
  steps/             # Per-form step logic (Ayushman, insurance, etc.)
  utils/             # Utilities (e.g., intent detection)
  main.py            # Flask app entrypoint
  requirements.txt   # Python dependencies
```

## Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Start Chrome in debug mode:**
   (You may need a script like `start_chrome_debug.bat`)
3. **Run the backend:**
   ```bash
   python main.py
   ```

## Usage
- **POST** `/api/browser/execute`
  - Body:
    ```json
    {
      "user_prompt": "Apply for Ayushman Bharat",
      "form_data": { ... }
    }
    ```
  - The backend will detect the workflow and automate the form accordingly.

- **Other endpoints:**
  - `/api/browser/submit_input` — For OTP or other user input
  - `/api/browser/status` — Get current browser state
  - `/api/browser/reset` — Reset the browser session

## Adding a New Form
1. Create a new step module in `steps/` (e.g., `steps/passport_steps.py`).
2. Add a prompt builder method in `browser_toolkit/prompt_builder.py`.
3. Update `utils/intent_detection.py` to map new user prompts to your form type.

## License
MIT 