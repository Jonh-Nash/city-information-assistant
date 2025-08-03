from typing import Any
import httpx
import asyncio
import json
from langchain_core.tools import tool
from ...domain.agent.tool_interface import ToolInterface, ToolResult

@tool
def get_local_time(timezone: str) -> str:
    """指定されたタイムゾーンの現地時間を取得します。
    
    Args:
        timezone: IANA タイムゾーン名（例: Asia/Tokyo, America/New_York, Europe/London）
        
    Returns:
        WorldTimeAPIからの現地時間情報のJSON文字列
    """
    async def fetch_time():
        try:
            url = f"http://worldtimeapi.org/api/timezone/{timezone}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"WorldTimeAPI returned status {response.status_code}")
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")
    
    try:
        data = asyncio.run(fetch_time())
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        # エラー時は具体的な使用方法を示す
        error_msg = f"Error: {str(e)}\n\n"
        error_msg += "IANA タイムゾーン名を使用してください。形式: 地域/都市\n"
        error_msg += "例:\n"
        error_msg += "- Asia/Tokyo (東京)\n"
        error_msg += "- America/New_York (ニューヨーク)\n" 
        error_msg += "- Europe/London (ロンドン)\n"
        error_msg += "- Europe/Paris (パリ)\n"
        error_msg += "- Australia/Sydney (シドニー)\n"
        error_msg += "- America/Los_Angeles (ロサンゼルス)\n"
        error_msg += "- Asia/Seoul (ソウル)\n"
        error_msg += "- Asia/Shanghai (上海)\n"
        error_msg += "\n完全なタイムゾーン一覧: http://worldtimeapi.org/api/timezone"
        raise Exception(error_msg)

class TimeToolImpl(ToolInterface):
    """時間ツールの実装"""
    
    @property
    def name(self) -> str:
        return "TimeTool"
    
    @property
    def description(self) -> str:
        return "指定されたタイムゾーンの現地時間を取得します。Please check the spelling or use format 'Asia/Tokyo' (e.g., Tokyo,JP)."
    
    def get_langchain_tool(self) -> Any:
        return get_local_time
    
    def execute(self, timezone: str, **kwargs) -> ToolResult:
        """現地時間を取得して結果オブジェクトを返す"""
        try:
            # WorldTimeAPIを直接呼び出し
            result = get_local_time(timezone)
            return ToolResult(
                success=True,
                data=result
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error_message=str(e),
                error_type="retryable"
            )