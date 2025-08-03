from pydantic import BaseModel
from typing import Optional

class Weather(BaseModel):
    city: str
    temperature: float
    description: str
    humidity: float
    feels_like: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    country: Optional[str] = None