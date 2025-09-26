import requests
from .llm_client import LLMClient

class OllamaClient(LLMClient):
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host

    async def query(self, prompt: str, model: str = "phi3:mini") -> str:
        url = f"{self.host}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["response"].strip()
