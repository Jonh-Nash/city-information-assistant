from datetime import datetime
from dataclasses import dataclass

@dataclass
class Conversation:
    id: str
    title: str
    created_at: datetime
    updated_at: datetime