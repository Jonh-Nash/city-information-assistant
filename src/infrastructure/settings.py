"""
アプリケーション全体の設定
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """アプリケーション設定"""
    
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""), description="PostgreSQL 接続 URL")
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""), description="OpenAI API キー（オプション）")
    openweather_api_key: str = Field(default_factory=lambda: os.getenv("OPENWEATHER_API_KEY", ""), description="OpenWeatherMap API キー")
