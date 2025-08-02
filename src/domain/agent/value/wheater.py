from pydantic import BaseModel

class Weather(BaseModel):
    city: str
    temperature: float
    description: str
    humidity: float