from datetime import datetime

class User:

    id: str
    username: str
    email: str
    created_at: datetime

    def verify_password(self, password: str) -> bool:
        return self.password == password
