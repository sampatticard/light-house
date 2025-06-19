# app/main.py

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from app.actions import ActionName, PROMPT_TEMPLATES
from app.schemas import ACTION_PARAM_MODELS
from app.ollama_client import query_ollama
from app.browseruse_agent import run_browser_actions
import json

app = FastAPI(title="Sampatti Lighthouse API")

class ActionRequest(BaseModel):
    # This model is dynamic: we’ll validate per-action in the endpoint.
    pass

@app.post("/action/{action_name}")
async def do_action(
    action_name: ActionName = Path(..., description="One of the predefined actions"),
    params: dict = None
):
    """
    Execute a predefined browseruse action via local SLM + Playwright.
    """
    # 1. Validate params via the corresponding Pydantic model
    ParamModel = ACTION_PARAM_MODELS.get(action_name)
    if ParamModel is None:
        raise HTTPException(status_code=400, detail="No parameters model for this action")
    try:
        # Pydantic validation
        parsed = ParamModel(**(params or {}))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 2. Build prompt
    template = PROMPT_TEMPLATES.get(action_name)
    if template is None:
        raise HTTPException(status_code=500, detail="No prompt template configured")
    prompt = template.format(**parsed.dict())

    # 3. Query local Ollama SLM
    # Optionally set temperature=0 or low to reduce randomness
    raw_output = query_ollama(prompt)
    # 4. Parse JSON
    try:
        actions_list = json.loads(raw_output)
    except json.JSONDecodeError as e:
        # If malformed, optionally try a repair prompt or return error
        raise HTTPException(status_code=500, detail=f"SLM output not valid JSON: {e}: {raw_output}")

    # 5. Validate each action via Pydantic DSL models
    from app.browseruse_agent import (
        NavigateAction, ClickAction, TypeAction, WaitAction, ExtractAction
    )
    validated_actions = []
    for obj in actions_list:
        action_type = obj.get("action")
        try:
            if action_type == "navigate":
                act = NavigateAction(**obj)
                # Additional: validate domain again
                from urllib.parse import urlparse
                domain = urlparse(act.url).netloc
                # Ensure domain matches the whitelisted domain(s) from params if applicable
                # E.g., for EXTRACT_RATE_BANK, ensure domain == parsed.bank_domain
                if action_name == ActionName.EXTRACT_RATE_BANK:
                    if domain != parsed.bank_domain:
                        raise ValueError(f"Navigate domain {domain} not allowed for this action")
            elif action_type == "click":
                act = ClickAction(**obj)
            elif action_type == "type":
                act = TypeAction(**obj)
            elif action_type == "wait":
                act = WaitAction(**obj)
            elif action_type == "extract":
                act = ExtractAction(**obj)
            else:
                raise ValueError(f"Unknown action type: {action_type}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Action validation error: {e}")
        validated_actions.append(act)

    # 6. Execute via Playwright
    try:
        results = run_browser_actions(validated_actions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browser execution error: {e}")

    # 7. Summarize if desired
    summary = None
    try:
        summary_prompt = (
            "Summarize the following extracted data in concise terms:\n"
            + json.dumps(results, indent=2)
        )
        summary = query_ollama(summary_prompt)
    except Exception:
        summary = "Failed to summarize results."

    return {"actions": [a.dict() for a in validated_actions], "results": results, "summary": summary}

#Auto-Form Parsing Endpoint
from fastapi import FastAPI, UploadFile, File, Form
from app.form_parser import parse_uploaded_form
from fastapi.responses import JSONResponse
@app.post("/parse/{form_type}")
async def parse_form(form_type: str, file: UploadFile = File(...)):
    """
    Upload a document to auto-parse fields for the given form_type.
    """
    try:
        result = await parse_uploaded_form(form_type, file)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(content={"fields": result})