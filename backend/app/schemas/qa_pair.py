"""Q&Aペアスキーマ"""
from pydantic import BaseModel
from typing import Optional


class QAPairRequest(BaseModel):
    """Q&Aペアリクエスト"""
    question: str
    answer: str


class QAPairResponse(BaseModel):
    """Q&Aペアレスポンス"""
    question: str
    answer: Optional[str]
    order: int

    class Config:
        from_attributes = True
