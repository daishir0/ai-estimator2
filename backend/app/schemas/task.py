from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.estimate import EstimateResponse


class TaskResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_file_path: Optional[str] = None

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class TaskResultResponse(BaseModel):
    id: str
    status: str
    estimates: List[EstimateResponse]
    subtotal: float
    tax: float
    total: float
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
