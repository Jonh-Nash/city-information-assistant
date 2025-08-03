"""
アプリケーション全体の設定
"""
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL", description="PostgreSQL 接続 URL")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY", description="OpenAI API キー")
    openweather_api_key: str = Field(..., env="OPENWEATHER_API_KEY", description="OpenWeatherMap API キー")

    class Config:
        env_file = ".env"
