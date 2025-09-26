from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    async def query(self, prompt: str, model: str = None) -> str:
        pass
