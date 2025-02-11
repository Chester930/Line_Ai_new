from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String(1000), nullable=False)  # 使用 content 作為消息內容
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 關聯到用戶
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, role={self.role})>" 