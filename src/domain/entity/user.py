from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:

    id: str
    username: str
    email: str
    password: str
    created_at: datetime

    def verify_password(self, password: str) -> bool:
        return self.password == password
