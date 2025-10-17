"""メッセージモデル（見積り調整用の会話履歴）"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant / agent
    content = Column(Text, nullable=False)  # Markdown想定
    created_at = Column(DateTime(timezone=True), server_default=func.now())

