from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    """ツール実行結果"""
    success: bool  # 成功/失敗
    data: Optional[Any] = None  # 成功時の結果データ
    error_message: Optional[str] = None  # 失敗時のエラーメッセージ
    error_type: Optional[str] = None  # エラーの種類（retryable/non-retryable等）
    tool_name: Optional[str] = None  # 実行されたツール名

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
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """ツールを実行して結果オブジェクトを返す"""
        pass