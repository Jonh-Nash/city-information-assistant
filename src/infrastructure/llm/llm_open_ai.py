from typing import List, Dict, Any
from ...domain.agent.llm_interface import LLMInterface

class LLMOpenAI(LLMInterface):
    """OpenAI LLMの実装（モック実装）"""
    
    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """
        メッセージリストからレスポンスを生成
        現在はモック実装で固定レスポンスを返す
        """
        # 最後のメッセージの内容を取得
        if messages:
            last_message = messages[-1].get("content", "")
            if "天気" in last_message or "weather" in last_message.lower():
                return "天気情報を取得するために天気ツールを使用します。"
        
        return "こんにちは！何についてお話ししましょうか？"