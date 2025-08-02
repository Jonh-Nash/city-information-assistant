from typing import Any
from langchain_core.tools import tool
from ...domain.agent.value.wheater import Weather
from ...domain.agent.tool_interface import ToolInterface

@tool
def get_weather(city: str) -> str:
    """指定された都市の天気情報を取得します。
    
    Args:
        city: 天気情報を取得したい都市名（日本語）
        
    Returns:
        天気情報の文字列
    """
    # モックデータ
    mock_data = {
        "東京": Weather(city="東京", temperature=25.0, description="晴れ", humidity=60.0),
        "大阪": Weather(city="大阪", temperature=28.0, description="曇り", humidity=70.0),
        "京都": Weather(city="京都", temperature=23.0, description="小雨", humidity=80.0),
        "名古屋": Weather(city="名古屋", temperature=22.0, description="曇り", humidity=65.0),
        "福岡": Weather(city="福岡", temperature=26.0, description="晴れ", humidity=55.0),
        "札幌": Weather(city="札幌", temperature=18.0, description="小雨", humidity=75.0),
    }
    
    # 指定された都市のデータがあれば返す、なければデフォルトデータ
    weather = mock_data.get(city, Weather(
        city=city, 
        temperature=20.0, 
        description="晴れ", 
        humidity=65.0
    ))
    
    return f"{weather.city}の天気は{weather.description}、気温は{weather.temperature}度、湿度は{weather.humidity}%です。"

class WeatherToolImpl(ToolInterface):
    """天気ツールの実装"""
    
    @property
    def name(self) -> str:
        return "get_weather"
    
    @property
    def description(self) -> str:
        return "指定された都市の天気情報を取得します"
    
    def get_langchain_tool(self) -> Any:
        return get_weather