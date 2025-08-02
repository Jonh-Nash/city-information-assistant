from datetime import datetime
from dataclasses import dataclass

@dataclass
class Message:
    id: str
    conversation_id: str
    content: str
    role: str  # "user" or "assistant"
    created_at: datetime