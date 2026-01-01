"""
Market data candle model
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, String, DateTime, Numeric, Index, UniqueConstraint
)
from sqlalchemy.orm import validates
from core.db import Base


class MarketCandle(Base):
    """Market candle/ohlcv data model"""
    __tablename__ = "market_candles"
    
    id = Column(String, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # OHLCV data
    open = Column(Numeric(precision=20, scale=8), nullable=False)
    high = Column(Numeric(precision=20, scale=8), nullable=False)
    low = Column(Numeric(precision=20, scale=8), nullable=False)
    close = Column(Numeric(precision=20, scale=8), nullable=False)
    volume = Column(Numeric(precision=20, scale=8), nullable=False)
    
    # Unique constraint for symbol+timeframe+timestamp
    __table_args__ = (
        UniqueConstraint('symbol', 'timeframe', 'timestamp', name='uq_symbol_timeframe_timestamp'),
        Index('idx_candle_lookup', 'symbol', 'timeframe', 'timestamp'),
        Index('idx_candle_symbol_time', 'symbol', 'timeframe', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MarketCandle(symbol={self.symbol}, timeframe={self.timeframe}, timestamp={self.timestamp})>"
    
    @validates('open', 'high', 'low', 'close', 'volume')
    def validate_numeric_fields(self, key, value):
        """Validate numeric fields are positive"""
        if value is not None:
            try:
                decimal_value = Decimal(str(value))
                if decimal_value < 0:
                    raise ValueError(f"{key} must be positive")
                return decimal_value
            except (ValueError, TypeError):
                raise ValueError(f"{key} must be a valid numeric value")
        return value
    
    @classmethod
    def create_from_dict(cls, symbol: str, timeframe: str, timestamp: datetime, data: dict) -> 'MarketCandle':
        """Create MarketCandle instance from dictionary data"""
        return cls(
            id=f"{symbol}_{timeframe}_{timestamp.isoformat()}",
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            open=Decimal(str(data.get('open', 0))),
            high=Decimal(str(data.get('high', 0))),
            low=Decimal(str(data.get('low', 0))),
            close=Decimal(str(data.get('close', 0))),
            volume=Decimal(str(data.get('volume', 0)))
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat(),
            'open': float(self.open),
            'high': float(self.high),
            'low': float(self.low),
            'close': float(self.close),
            'volume': float(self.volume)
        }
    
    @property
    def price_range(self) -> float:
        """Get price range (high - low)"""
        return float(self.high - self.low)
    
    @property
    def body_size(self) -> float:
        """Get candle body size (abs(open - close))"""
        return abs(float(self.open - self.close))
    
    @property
    def upper_wick(self) -> float:
        """Get upper wick size (high - max(open, close))"""
        return float(self.high - max(self.open, self.close))
    
    @property
    def lower_wick(self) -> float:
        """Get lower wick size (min(open, close) - low)"""
        return float(min(self.open, self.close) - self.low)
    
    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish (close > open)"""
        return float(self.close) > float(self.open)
    
    @property
    def is_bearish(self) -> bool:
        """Check if candle is bearish (close < open)"""
        return float(self.close) < float(self.open)