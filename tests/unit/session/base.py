# src/shared/session/base.py

from datetime import datetime
import uuid

class Message:
    def __init__(self, role: str, content: str):
        self.message_id = str(uuid.uuid4())
        self.role = role
        self.content = content
        self.timestamp = datetime.now()

class Session:
    def __init__(self, user_id: str, metadata: dict):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.metadata = metadata
        self.messages = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, message: Message):
        self.messages.append(message)
        self.updated_at = datetime.now()

    def clear_messages(self):
        self.messages.clear()
        self.updated_at = datetime.now()

    def get_messages(self, limit: int = None):
        return self.messages[-limit:] if limit else self.messages