"""見積り調整チャット用スキーマ"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    message: Optional[str] = None
    intent: Optional[str] = None  # fit_budget, scope_reduce, unit_cost_change, risk_buffer
    params: Optional[Dict[str, Any]] = None
    estimates: Optional[List[Dict[str, Any]]] = None  # フロントからの現在表示中の見積り（任意）


class ChatSuggestion(BaseModel):
    label: str
    payload: Dict[str, Any]


class ChatEstimateItem(BaseModel):
    deliverable_name: str
    deliverable_description: Optional[str]
    person_days: float
    amount: float
    reasoning: Optional[str]


class ChatResponse(BaseModel):
    reply_md: str
    suggestions: Optional[List[ChatSuggestion]] = None
    proposals: Optional[List[Dict[str, Any]]] = None  # 提案カード（2ステップUX）
    estimates: Optional[List[ChatEstimateItem]] = None
    totals: Optional[Dict[str, float]] = None
    version: Optional[int] = None
