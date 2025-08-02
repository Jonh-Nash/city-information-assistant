from abc import ABC, abstractmethod
from typing import Any

class LLMInterface(ABC):
    @abstractmethod
    def bind_tools(self) -> Any:
        pass