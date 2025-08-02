from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMInterface(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        pass
