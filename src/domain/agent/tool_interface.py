from abc import ABC, abstractmethod
from typing import Any

class ToolInterface(ABC):
    """ツールの基底インターフェース"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """ツール名を返す"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """ツールの説明を返す"""
        pass
    
    @abstractmethod
    def get_langchain_tool(self) -> Any:
        """LangChainのツールオブジェクトを返す"""
        pass