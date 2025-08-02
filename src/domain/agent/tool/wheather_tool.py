from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..value.wheater import Weather

class WeatherTool(ABC):
    @abstractmethod
    async def execute(self, city: str) -> Weather:
        pass