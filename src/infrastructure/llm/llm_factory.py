import os
from typing import Any
from langchain_openai import ChatOpenAI
from ..settings import Settings
from ...domain.agent.llm_interface import LLMInterface

class OpenAIFactory(LLMInterface):
    """OpenAI LLMインスタンスを生成するファクトリー"""
    
    @staticmethod
    def create_llm_instance(
        model_name: str = "gpt-3.5-turbo", 
        temperature: float = 0.7
    ) -> Any:
        # 設定からAPIキーを取得
        settings = Settings()
        api_key = settings.openai_api_key
        
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it with: export OPENAI_API_KEY='your_api_key_here'"
            )
        
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key
        )