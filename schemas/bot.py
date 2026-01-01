"""
Bot related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from models.bot import BotState, AssetType, StrategyId


class BotBase(BaseModel):
    """Base bot schema"""
    name: str = Field(..., description="Bot name")
    asset_type: AssetType
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    timeframe: str = Field(..., description="Timeframe (e.g., 1h, 4h, 1d)")
    strategy_id: StrategyId
    interval_seconds: int = Field(default=60, ge=30, le=86400, description="Execution interval in seconds")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Strategy parameters")


class BotCreate(BotBase):
    """Bot creation schema"""
    pass


class BotUpdate(BaseModel):
    """Bot update schema"""
    name: Optional[str] = None
    asset_type: Optional[AssetType] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    strategy_id: Optional[StrategyId] = None
    interval_seconds: Optional[int] = Field(default=None, ge=30, le=86400)
    params: Optional[Dict[str, Any]] = None


class BotResponse(BotBase):
    """Bot response schema"""
    id: str
    user_id: str
    state: BotState
    scheduler_job_id: Optional[str] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotStatusResponse(BaseModel):
    """Bot status response schema"""
    id: str
    name: str
    state: BotState
    last_run_at: Optional[datetime] = None
    is_running: bool
    can_start: bool
    can_stop: bool


class BotStartRequest(BaseModel):
    """Bot start request schema"""
    pass


class BotStopRequest(BaseModel):
    """Bot stop request schema"""
    pass


class BotStartResponse(BaseModel):
    """Bot start response schema"""
    status: str
    job_id: str
    message: str


class BotStopResponse(BaseModel):
    """Bot stop response schema"""
    status: str
    message: str