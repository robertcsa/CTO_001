"""
Bot model for trading bot configuration and state
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from core.db import Base


class BotState(PyEnum):
    """Bot execution states"""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    PAUSED = "paused"


class AssetType(PyEnum):
    """Supported asset types"""
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCKS = "stocks"


class StrategyId(PyEnum):
    """Available trading strategies"""
    BLUE_SKY = "blue_sky"


class Bot(Base):
    """Trading bot model"""
    __tablename__ = "bots"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    strategy_id = Column(Enum(StrategyId), nullable=False)
    state = Column(Enum(BotState), default=BotState.STOPPED, nullable=False)
    scheduler_job_id = Column(String, nullable=True)
    interval_seconds = Column(Integer, nullable=False, default=60)
    params = Column(JSON, nullable=True)  # Strategy parameters
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="bots")
    indicators = relationship("IndicatorSnapshot", back_populates="bot", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="bot", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="bot", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Bot(id={self.id}, name={self.name}, state={self.state.value})>"
    
    @property
    def is_running(self) -> bool:
        """Check if bot is currently running"""
        return self.state == BotState.RUNNING
    
    @property
    def can_start(self) -> bool:
        """Check if bot can be started"""
        return self.state in [BotState.STOPPED, BotState.ERROR]
    
    @property
    def can_stop(self) -> bool:
        """Check if bot can be stopped"""
        return self.state in [BotState.RUNNING, BotState.PAUSED]
    
    def update_state(self, new_state: BotState):
        """Update bot state with validation"""
        valid_transitions = {
            BotState.STOPPED: [BotState.RUNNING, BotState.ERROR],
            BotState.RUNNING: [BotState.STOPPED, BotState.PAUSED, BotState.ERROR],
            BotState.PAUSED: [BotState.RUNNING, BotState.STOPPED, BotState.ERROR],
            BotState.ERROR: [BotState.STOPPED]
        }
        
        if new_state not in valid_transitions.get(self.state, []):
            raise ValueError(f"Invalid state transition from {self.state.value} to {new_state.value}")
        
        self.state = new_state
        self.updated_at = datetime.utcnow()
    
    def get_params(self, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get bot parameters with defaults"""
        return self.params or default or {}
    
    def set_params(self, params: Dict[str, Any]):
        """Set bot parameters"""
        self.params = params
        self.updated_at = datetime.utcnow()