"""
Order model for paper trading orders
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from core.db import Base


class OrderSide(PyEnum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(PyEnum):
    """Order statuses"""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PositionState(PyEnum):
    """Position states"""
    NONE = "none"
    LONG = "long"
    SHORT = "short"


class Order(Base):
    """Paper trading order model"""
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False, index=True)
    signal_id = Column(String, ForeignKey("signals.id"), nullable=True, index=True)
    side = Column(String, nullable=False, index=True)  # BUY/SELL
    quantity = Column(Numeric(precision=20, scale=8), nullable=False)
    price = Column(Numeric(precision=20, scale=8), nullable=False)
    status = Column(String, default=OrderStatus.OPEN.value, nullable=False)
    position_state = Column(String, default=PositionState.NONE.value, nullable=False)
    entry_price = Column(Numeric(precision=20, scale=8), nullable=True)
    exit_price = Column(Numeric(precision=20, scale=8), nullable=True)
    pnl = Column(Numeric(precision=20, scale=8), default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional metadata
    meta = Column('metadata', nullable=True)  # JSON metadata
    
    # Relationships
    bot = relationship("Bot", back_populates="orders")
    signal = relationship("Signal", back_populates="orders")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_bot_status', 'bot_id', 'status'),
        Index('idx_order_signal', 'signal_id'),
        Index('idx_order_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, bot_id={self.bot_id}, side={self.side}, status={self.status}, pnl={self.pnl})>"
    
    @classmethod
    def create(
        cls,
        bot_id: str,
        side: OrderSide,
        quantity: float,
        price: float,
        signal_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> 'Order':
        """Create order instance"""
        return cls(
            id=f"{bot_id}_{side.value}_{datetime.utcnow().isoformat()}",
            bot_id=bot_id,
            signal_id=signal_id,
            side=side.value,
            quantity=quantity,
            price=price,
            meta=meta
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'bot_id': self.bot_id,
            'signal_id': self.signal_id,
            'side': self.side,
            'quantity': float(self.quantity),
            'price': float(self.price),
            'status': self.status,
            'position_state': self.position_state,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'exit_price': float(self.exit_price) if self.exit_price else None,
            'pnl': float(self.pnl),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'meta': self.metadata
        }
    
    def is_open(self) -> bool:
        """Check if order is open"""
        return self.status == OrderStatus.OPEN.value
    
    def is_closed(self) -> bool:
        """Check if order is closed"""
        return self.status == OrderStatus.CLOSED.value
    
    def is_cancelled(self) -> bool:
        """Check if order is cancelled"""
        return self.status == OrderStatus.CANCELLED.value
    
    def is_buy_order(self) -> bool:
        """Check if order is a buy order"""
        return self.side == OrderSide.BUY.value
    
    def is_sell_order(self) -> bool:
        """Check if order is a sell order"""
        return self.side == OrderSide.SELL.value
    
    def get_pnl_percentage(self) -> Optional[float]:
        """Get P&L as percentage"""
        if self.entry_price and self.exit_price and self.entry_price != 0:
            if self.is_buy_order():
                return ((self.exit_price - self.entry_price) / self.entry_price) * 100
            else:
                return ((self.entry_price - self.exit_price) / self.entry_price) * 100
        return None
    
    def close_order(self, exit_price: float, pnl: Optional[float] = None):
        """Close the order"""
        self.status = OrderStatus.CLOSED.value
        self.exit_price = exit_price
        if pnl is not None:
            self.pnl = pnl
        else:
            # Calculate P&L if not provided
            if self.entry_price:
                if self.is_buy_order():
                    self.pnl = (exit_price - self.entry_price) * float(self.quantity)
                else:
                    self.pnl = (self.entry_price - exit_price) * float(self.quantity)
        self.updated_at = datetime.utcnow()