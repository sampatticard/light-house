import subprocess
from .llm_client import LLMClient

class MCPClient(LLMClient):
    def __init__(self, model_path: str = "models/phi3-mini.gguf", temperature: float = 0.0):
        self.model_path = model_path
        self.temperature = temperature

    async def query(self, prompt: str, model: str = None) -> str:
        cmd = [
            "llama.cpp",
            "-m", self.model_path,
            "--temp", str(self.temperature),
            "-p", prompt
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
