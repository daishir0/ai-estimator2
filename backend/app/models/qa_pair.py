"""Q&Aペアモデル"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from app.db.database import Base


class QAPair(Base):
    """Q&Aペアテーブル"""
    __tablename__ = "qa_pairs"

    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
