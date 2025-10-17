"""見積りモデル"""
from sqlalchemy import Column, String, Float, Text, ForeignKey
from app.db.database import Base


class Estimate(Base):
    """見積りテーブル"""
    __tablename__ = "estimates"

    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    deliverable_name = Column(String(200), nullable=False)
    deliverable_description = Column(Text, nullable=True)
    person_days = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)  # 後方互換性のため残す
    reasoning_breakdown = Column(Text, nullable=True)  # 工数内訳
    reasoning_notes = Column(Text, nullable=True)  # 根拠・備考
