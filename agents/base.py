from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    @abstractmethod
    def analyze(self, sku: str, period_days: int) -> Dict[str, Any]:
        pass