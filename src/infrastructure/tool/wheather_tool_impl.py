from typing import Any
import httpx
import asyncio
from langchain_core.tools import tool
from ...domain.agent.value.wheater import Weather
from ...domain.agent.tool_interface import ToolInterface, ToolResult
from ...infrastructure.settings import Settings

# 設定インスタンス
settings = Settings()

async def fetch_weather_data(city: str) -> dict:
    """OpenWeatherMap APIから天気データを取得"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.openweather_api_key,
        "units": "metric"  # 摂氏温度で取得（説明は英語のまま）
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

@tool
def get_weather(city: str) -> str:
    """指定された都市の天気情報を取得します。
    
    Args:
        city: 天気情報を取得したい都市名（日本語、英語、その他言語対応）
        
    Returns:
        天気情報の文字列
    """
    try:
        # 都市名で直接APIを呼び出し
        weather_data = asyncio.run(fetch_weather_data(city))
        
        # レスポンスから必要な情報を抽出
        main = weather_data["main"]
        weather_info = weather_data["weather"][0]
        wind = weather_data.get("wind", {})
        sys_info = weather_data.get("sys", {})
        
        # APIレスポンスから実際の都市名を取得
        actual_city_name = weather_data.get("name", city)
        
        # Weatherオブジェクトを作成
        weather = Weather(
            city=actual_city_name,
            temperature=round(main["temp"], 1),
            description=weather_info["description"],  # 英語のまま使用
            humidity=main["humidity"],
            feels_like=round(main.get("feels_like", main["temp"]), 1),
            pressure=main.get("pressure"),
            wind_speed=wind.get("speed"),
            country=sys_info.get("country")
        )
        
        # Weatherオブジェクトの情報をJSON文字列として返す
        return weather.model_dump_json()
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "Invalid OpenWeatherMap API key. Please check your configuration."
        elif e.response.status_code == 404:
            return f"City '{city}' not found. Please check the spelling or use format 'City,CountryCode' (e.g., Tokyo,JP)."
        else:
            return f"Failed to fetch weather information (HTTP Error: {e.response.status_code})"
    except Exception as e:
        return f"Error occurred while fetching weather information: {str(e)}"

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
    
    def execute(self, city: str, **kwargs) -> ToolResult:
        """天気情報を取得して結果オブジェクトを返す"""
        try:
            # 都市名で直接APIを呼び出し
            weather_data = asyncio.run(fetch_weather_data(city))
            
            # レスポンスから必要な情報を抽出
            main = weather_data["main"]
            weather_info = weather_data["weather"][0]
            wind = weather_data.get("wind", {})
            sys_info = weather_data.get("sys", {})
            
            # APIレスポンスから実際の都市名を取得
            actual_city_name = weather_data.get("name", city)
            
            # Weatherオブジェクトを作成
            weather = Weather(
                city=actual_city_name,
                temperature=round(main["temp"], 1),
                description=weather_info["description"],
                humidity=main["humidity"],
                feels_like=round(main.get("feels_like", main["temp"]), 1),
                pressure=main.get("pressure"),
                wind_speed=wind.get("speed"),
                country=sys_info.get("country")
            )
            
            return ToolResult(
                success=True,
                data=weather.model_dump_json()
            )
            
        except httpx.HTTPStatusError as e:
            error_type = "retryable" if e.response.status_code in [500, 502, 503, 504] else "non-retryable"
            
            if e.response.status_code == 401:
                error_msg = "Invalid OpenWeatherMap API key. Please check your configuration."
            elif e.response.status_code == 404:
                error_msg = f"City '{city}' not found. Please check the spelling or use format 'City,CountryCode' (e.g., Tokyo,JP)."
                error_type = "retryable"  # 都市名の問題は修正可能
            else:
                error_msg = f"Failed to fetch weather information (HTTP Error: {e.response.status_code})"
            
            return ToolResult(
                success=False,
                error_message=error_msg,
                error_type=error_type
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error_message=f"Error occurred while fetching weather information: {str(e)}",
                error_type="retryable"
            )