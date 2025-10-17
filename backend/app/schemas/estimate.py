"""見積りスキーマ"""
from pydantic import BaseModel
from typing import Optional


class EstimateResponse(BaseModel):
    """見積りレスポンス"""
    deliverable_name: str
    deliverable_description: Optional[str]
    person_days: float
    amount: float
    reasoning: Optional[str]

    class Config:
        from_attributes = True
