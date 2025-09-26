from .ollama_client import OllamaClient
from .mcp_client import MCPClient
from .llm_client import LLMClient

def get_llm_client(llm_type: str) -> LLMClient:
    if llm_type == "ollama":
        return OllamaClient()
    elif llm_type == "mcp":
        return MCPClient()
    else:
        raise ValueError(f"Unknown LLM type: {llm_type}")
