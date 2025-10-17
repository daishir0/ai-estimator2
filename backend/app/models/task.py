from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    excel_file_path = Column(String(500))
    system_requirements = Column(Text)
    status = Column(String(20), default=TaskStatus.PENDING.value)
    error_message = Column(Text)
    result_file_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
