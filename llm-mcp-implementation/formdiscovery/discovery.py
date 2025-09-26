import json
from .form_discovery_result import FormDiscoveryResult
from llm.mcp_client import MCPClient

_DISCOVERY_PROMPT = """
You are a financial-forms assistant.
Given the user request, identify:

a canonical short form_type (snake_case, e.g. student_loan, home_loan)

the OFFICIAL URL where that form can be filled online.

Respond ONLY in JSON with keys form_type and form_url, no commentary.

User request:
""" + "{request}" + """
"""

mcp_client = MCPClient()

def discover_form(user_request: str) -> FormDiscoveryResult:
    raw = mcp_client.query(_DISCOVERY_PROMPT.format(request=user_request))
    try:
        data = json.loads(raw)
        return data  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Form discovery failed: {e} | Output: {raw}")
