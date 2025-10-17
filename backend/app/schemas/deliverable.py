"""成果物スキーマ"""
from pydantic import BaseModel
from typing import Optional


class Deliverable(BaseModel):
    """成果物"""
    name: str
    description: Optional[str] = None
