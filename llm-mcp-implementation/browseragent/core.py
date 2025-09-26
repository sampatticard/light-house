import json
import logging
from llm.mcp_client import MCPClient
from .actions_union import BrowserAction
from .navigate_action import NavigateAction
from .click_action import ClickAction
from .type_action import TypeAction
from .wait_action import WaitAction
from .extract_action import ExtractAction
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List

mcp_client = MCPClient()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_ACTION_GEN_PROMPT = """
You are a browser-automation generator.
Output ONLY a JSON array of actions using the DSL:

navigate: {{"action":"navigate","url":""}}

click:    {{"action":"click","selector":"","wait_for":null}}

type:     {{"action":"type","selector":"","text":"","clear":true,"delay":null}}

wait:     {{"action":"wait","selector":"","timeout":ms}}

extract:  {{"action":"extract","selector":"","attribute":null}}

Constraints:

Stay strictly inside {{domain}} domain.

Your goal: {{goal}}.

Return ONLY the JSON array, no commentary.
"""

def generate_actions(goal: str, domain: str) -> List[BrowserAction]:
    prompt = _ACTION_GEN_PROMPT.format(goal=goal, domain=domain)
    raw = mcp_client.query(prompt)
    return _validate_and_parse_actions(raw)

def _validate_and_parse_actions(raw_json: str) -> List[BrowserAction]:
    try:
        arr = json.loads(raw_json)
        if not isinstance(arr, list):
            raise ValueError("Not a JSON array")
    except Exception as e:
        raise RuntimeError(f"Invalid JSON from MCP: {e} | {raw_json}")

    parsed: List[BrowserAction] = []
    for obj in arr:
        typ = obj.get("action")
        try:
            if typ == "navigate": parsed.append(NavigateAction(**obj))
            elif typ == "click": parsed.append(ClickAction(**obj))
            elif typ == "type": parsed.append(TypeAction(**obj))
            elif typ == "wait": parsed.append(WaitAction(**obj))
            elif typ == "extract": parsed.append(ExtractAction(**obj))
            else: raise ValueError(f"Unknown action {typ}")
        except Exception as ve:
            raise RuntimeError(f"DSL validation failed: {ve}")
    return parsed

def run_browser_actions(actions: List[BrowserAction], headless: bool = True, timeout_ms: int = 30000) -> List[dict]:
    results: List[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)
        for act in actions:
            try:
                if isinstance(act, NavigateAction): page.goto(str(act.url))
                elif isinstance(act, ClickAction):
                    page.click(act.selector)
                    if act.wait_for: page.wait_for_selector(act.wait_for, timeout=timeout_ms)
                elif isinstance(act, TypeAction):
                    if act.clear: page.fill(act.selector, "")
                    if act.delay: page.type(act.selector, act.text, delay=act.delay)
                    else: page.fill(act.selector, act.text)
                elif isinstance(act, WaitAction):
                    if act.selector: page.wait_for_selector(act.selector, timeout=act.timeout)
                    else: page.wait_for_timeout(act.timeout)
                elif isinstance(act, ExtractAction):
                    if act.attribute:
                        val = page.locator(act.selector).get_attribute(act.attribute)
                        results.append({"selector": act.selector, "attribute": act.attribute, "value": val})
                    else:
                        txt = page.locator(act.selector).inner_text()
                        results.append({"selector": act.selector, "text": txt})
            except PlaywrightTimeoutError as te:
                results.append({"error": f"Timeout on {act.action}: {te}"})
            except Exception as ex:
                results.append({"error": f"Failed {act.action}: {ex}"})
        browser.close()
    return results

def ensure_allowed_domains(actions: List[BrowserAction], allowed: list[str]) -> None:
    for act in actions:
        if isinstance(act, NavigateAction):
            domain = urlparse(str(act.url)).netloc
            if domain not in allowed:
                raise ValueError(f"Navigate domain '{domain}' not allowed.")
