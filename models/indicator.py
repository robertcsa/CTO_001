"""
Indicator snapshot model for storing calculated technical indicators
"""
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from core.db import Base


class IndicatorSnapshot(Base):
    """Technical indicator snapshot model"""
    __tablename__ = "indicator_snapshots"
    
    id = Column(String, primary_key=True)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    indicator_type = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)  # Store indicator values as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bot = relationship("Bot", back_populates="indicators")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_indicator_bot_time', 'bot_id', 'timestamp', 'indicator_type'),
        Index('idx_indicator_type_time', 'indicator_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<IndicatorSnapshot(bot_id={self.bot_id}, type={self.indicator_type}, timestamp={self.timestamp})>"
    
    @classmethod
    def create(
        cls, 
        bot_id: str, 
        timestamp: datetime, 
        indicator_type: str, 
        value: Dict[str, Any]
    ) -> 'IndicatorSnapshot':
        """Create indicator snapshot instance"""
        return cls(
            id=f"{bot_id}_{indicator_type}_{timestamp.isoformat()}",
            bot_id=bot_id,
            timestamp=timestamp,
            indicator_type=indicator_type,
            value=value
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'bot_id': self.bot_id,
            'timestamp': self.timestamp.isoformat(),
            'indicator_type': self.indicator_type,
            'value': self.value,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def key(self) -> str:
        """Get indicator key for caching"""
        return f"{self.indicator_type}:{self.timestamp.isoformat()}"


class IndicatorType:
    """Supported indicator types"""
    SUPPORT_RESISTANCE = "support_resistance"
    LINEAR_REGRESSION = "linear_regression"
    VOLATILITY = "volatility"
    ATR = "atr"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Get list of supported indicator types"""
        return [
            cls.SUPPORT_RESISTANCE,
            cls.LINEAR_REGRESSION,
            cls.VOLATILITY,
            cls.ATR,
            cls.RSI,
            cls.MACD,
            cls.BOLLINGER_BANDS
        ]