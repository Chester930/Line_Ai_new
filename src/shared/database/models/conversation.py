from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model = Column(String(50))  # 使用的 AI 模型
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")
    
    # 關聯
    user = relationship("User", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation {self.id}>" 