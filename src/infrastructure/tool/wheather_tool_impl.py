from ...domain.agent.tool.wheather_tool import WeatherTool
from ...domain.agent.value.wheater import Weather

class WeatherToolImpl(WeatherTool):
    """天気ツールの実装（モック実装）"""
    
    async def execute(self, city: str) -> Weather:
        """
        指定された都市の天気情報を取得
        現在はモック実装で固定データを返す
        """
        # モックデータ
        mock_data = {
            "東京": Weather(city="東京", temperature=25.0, description="晴れ", humidity=60.0),
            "大阪": Weather(city="大阪", temperature=28.0, description="曇り", humidity=70.0),
            "京都": Weather(city="京都", temperature=23.0, description="小雨", humidity=80.0),
        }
        
        # 指定された都市のデータがあれば返す、なければデフォルトデータ
        return mock_data.get(city, Weather(
            city=city, 
            temperature=20.0, 
            description="晴れ", 
            humidity=65.0
        ))