"""
Market data related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MarketCandleBase(BaseModel):
    """Base market candle schema"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandleResponse(MarketCandleBase):
    """Market candle response schema"""
    id: str

    class Config:
        from_attributes = True


class IndicatorResponse(BaseModel):
    """Technical indicator response schema"""
    id: str
    bot_id: str
    timestamp: datetime
    indicator_type: str
    value: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class MarketDataRequest(BaseModel):
    """Market data request schema"""
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe (e.g., 1h, 4h, 1d)")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of candles to fetch")


class IndicatorsRequest(BaseModel):
    """Indicators request schema"""
    bot_id: str
    limit: int = Field(default=50, ge=1, le=200, description="Number of indicators to fetch")
    indicator_type: Optional[str] = Field(default=None, description="Filter by indicator type")


class SupportResistance(BaseModel):
    """Support and resistance levels"""
    supports: List[Dict[str, float]]  # [{"price": 45000.0, "strength": 0.8}]
    resistances: List[Dict[str, float]]  # [{"price": 47000.0, "strength": 0.7}]


class LinearRegression(BaseModel):
    """Linear regression trend data"""
    slope: float
    intercept: float
    r2: float  # R-squared value
    points: List[Dict[str, float]]  # [{"x": 1, "y": price}, ...]


class Volatility(BaseModel):
    """Volatility indicators"""
    stdev: float  # Standard deviation
    atr: float  # Average True Range


class CandlesResponse(BaseModel):
    """Candles list response schema"""
    candles: List[CandleResponse]
    total: int
    symbol: str
    timeframe: str