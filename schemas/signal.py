"""
Signal related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from models.signal import SignalType


class SignalBase(BaseModel):
    """Base signal schema"""
    bot_id: str
    timestamp: datetime
    signal_type: SignalType
    confidence: float = Field(ge=0.0, le=1.0, description="Signal confidence (0.0 to 1.0)")
    reason: Optional[str] = Field(default=None, description="Human-readable reason for signal")


class SignalCreate(SignalBase):
    """Signal creation schema"""
    pass


class SignalResponse(SignalBase):
    """Signal response schema"""
    id: str
    inputs_hash: str
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SignalsListRequest(BaseModel):
    """Signals list request schema"""
    bot_id: str
    limit: int = Field(default=50, ge=1, le=200, description="Number of signals to fetch")
    signal_type: Optional[SignalType] = Field(default=None, description="Filter by signal type")
    start_date: Optional[datetime] = Field(default=None, description="Filter by start date")
    end_date: Optional[datetime] = Field(default=None, description="Filter by end date")


class SignalsResponse(BaseModel):
    """Signals list response schema"""
    signals: List[SignalResponse]
    total: int
    bot_id: str
    filters_applied: Dict[str, Any]


class SignalStats(BaseModel):
    """Signal statistics"""
    total_signals: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    avg_confidence: float
    high_confidence_signals: int  # confidence >= 0.8
    last_signal_at: Optional[datetime] = None


class SignalsStatsResponse(BaseModel):
    """Signals statistics response schema"""
    bot_id: str
    stats: SignalStats
    generated_at: datetime