"""成果物モデル"""
from sqlalchemy import Column, String, Text, ForeignKey
from app.db.database import Base


class Deliverable(Base):
    """成果物テーブル"""
    __tablename__ = "deliverables"

    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
