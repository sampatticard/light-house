# app/browseruse_agent.py

import json
import logging
import playwright.sync_api
from typing import List, Literal, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, HttpUrl, ValidationError
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.ollama_client import query_ollama

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# === DSL Models for Browser Actions ===

class NavigateAction(BaseModel):
    action: Literal["navigate"]
    url: HttpUrl

class ClickAction(BaseModel):
    action: Literal["click"]
    selector: str
    wait_for: Optional[str] = None  # CSS selector to wait for after click

class TypeAction(BaseModel):
    action: Literal["type"]
    selector: str
    text: str
    clear: Optional[bool] = True
    delay: Optional[int] = None  # milliseconds between keystrokes

class WaitAction(BaseModel):
    action: Literal["wait"]
    selector: Optional[str] = None  # if None, just sleep timeout
    timeout: Optional[int] = 5000  # ms

class ExtractAction(BaseModel):
    action: Literal["extract"]
    selector: str
    attribute: Optional[str] = None  # if None, extract inner_text

# Union type for convenience
BrowserAction = Union[NavigateAction, ClickAction, TypeAction, WaitAction, ExtractAction]


# === Function to Execute Actions via Playwright ===

# === Function to Generate Browser Actions via SLM ===

def generate_browser_actions(prompt: str, max_attempts: int = 2) -> List[BrowserAction]:
    """
    Given a prompt instructing the SLM to output a JSON array of browser actions
    following the DSL, call the local Ollama SLM, parse and validate the JSON.
    If parsing fails, will attempt to repair by re-prompting once.
    Raises RuntimeError on persistent failure.
    """
    raw = query_ollama(prompt)
    logger.info(f"Raw SLM output: {raw}")
    last_raw = raw
    for attempt in range(max_attempts):
        try:
            arr = json.loads(raw)
            if not isinstance(arr, list):
                raise ValueError("SLM output JSON is not a list")
            validated_actions: List[BrowserAction] = []
            for obj in arr:
                if not isinstance(obj, dict):
                    raise ValueError(f"Action is not an object: {obj}")
                action_type = obj.get("action")
                if action_type == "navigate":
                    act = NavigateAction(**obj)
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
                validated_actions.append(act)
            logger.info(f"Validated actions: {validated_actions}")
            return validated_actions
        except (json.JSONDecodeError, ValueError, ValidationError) as e:
            logger.warning(f"Failed to parse/validate actions (attempt {attempt+1}): {e}")
            if attempt + 1 < max_attempts:
                # Ask SLM to correct the output strictly as JSON array
                repair_prompt = (
                    "The previous response was not valid JSON or did not match the expected DSL schema. "
                    "Please output ONLY the corrected JSON array of actions, nothing else. "
                    "Here was the previous response:\n"
                    + last_raw
                )
                raw = query_ollama(repair_prompt)
                last_raw = raw
                logger.info(f"Repair attempt raw output: {raw}")
            else:
                break
    raise RuntimeError(f"Failed to generate valid browser actions after {max_attempts} attempts. Last output: {last_raw}")


# === Optional Helper: Domain Whitelist Validation ===

# app/browseruse_agent.py (patched excerpts)

from urllib.parse import urlparse

def run_browser_actions(
    actions: List[BrowserAction],
    headless: bool = True,
    timeout_ms: int = 30000
) -> List[dict]:
    results: List[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)
        for act in actions:
            typ = act.action
            try:
                if typ == "navigate":
                    url = str(act.url)
                    page.goto(url)
                elif typ == "click":
                    page.click(act.selector)
                    if act.wait_for:
                        page.wait_for_selector(act.wait_for, timeout=timeout_ms)
                elif typ == "type":
                    if act.clear:
                        try:
                            page.fill(act.selector, "")
                        except PlaywrightTimeoutError:
                            pass
                    if act.delay is not None:
                        page.type(act.selector, act.text, delay=act.delay)
                    else:
                        page.fill(act.selector, act.text)
                elif typ == "wait":
                    if act.selector:
                        page.wait_for_selector(act.selector, timeout=act.timeout or timeout_ms)
                    else:
                        page.wait_for_timeout(act.timeout or 1000)
                elif typ == "extract":
                    if act.attribute:
                        val = page.locator(act.selector).get_attribute(act.attribute)
                        results.append({
                            "action": "extract",
                            "selector": act.selector,
                            "attribute": act.attribute,
                            "value": val,
                        })
                    else:
                        text = page.locator(act.selector).inner_text()
                        results.append({
                            "action": "extract",
                            "selector": act.selector,
                            "text": text,
                        })
            except PlaywrightTimeoutError as e:
                info = act.model_dump() if hasattr(act, "model_dump") else act.dict()
                results.append({"error": f"Timeout on action {info}: {e}"})
            except Exception as e:
                info = act.model_dump() if hasattr(act, "model_dump") else act.dict()
                results.append({"error": f"Error on action {info}: {e}"})
        browser.close()
    return results

def validate_navigate_domains(actions: List[BrowserAction], allowed_domains: List[str]) -> None:
    for act in actions:
        if isinstance(act, NavigateAction):
            domain = urlparse(str(act.url)).netloc
            if domain not in allowed_domains:
                raise ValueError(f"Navigate domain '{domain}' not in allowed domains {allowed_domains}")


# === Example Usage ===
# (The FastAPI endpoint would build a prompt template, then:)
#
# from app.browseruse_agent import generate_browser_actions, run_browser_actions, validate_navigate_domains
#
# prompt = """You are a browser automation generator...
# Return ONLY a JSON array of actions..."""
# try:
#     actions = generate_browser_actions(prompt)
#     # Optionally validate domains:
#     allowed = ["examplebank.com"]
#     validate_navigate_domains(actions, allowed)
#     results = run_browser_actions(actions)
#     # Summarize if needed via query_ollama
# except Exception as e:
#     # Handle errors: return to frontend or log
#     logger.error(f"Browseruse flow failed: {e}")
