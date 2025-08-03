from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LocalTime(BaseModel):
    """都市の現地時間情報"""
    city: str
    country: Optional[str] = None
    timezone: str
    local_time: str
    formatted_time: str
    utc_offset: str
    is_dst: Optional[bool] = None