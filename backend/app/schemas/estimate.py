"""見積りスキーマ"""
from pydantic import BaseModel
from typing import Optional


class EstimateResponse(BaseModel):
    """見積りレスポンス"""
    deliverable_name: str
    deliverable_description: Optional[str]
    person_days: float
    amount: float
    reasoning: Optional[str] = None  # 後方互換性のため残す
    reasoning_breakdown: Optional[str] = None  # 工数内訳
    reasoning_notes: Optional[str] = None  # 根拠・備考

    class Config:
        from_attributes = True
