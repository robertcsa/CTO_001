"""
Order related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from models.order import OrderSide, OrderStatus, PositionState


class OrderBase(BaseModel):
    """Base order schema"""
    bot_id: str
    signal_id: Optional[str] = None
    side: OrderSide
    quantity: float = Field(gt=0, description="Order quantity")
    price: float = Field(gt=0, description="Order price")


class OrderCreate(OrderBase):
    """Order creation schema"""
    pass


class OrderResponse(OrderBase):
    """Order response schema"""
    id: str
    status: OrderStatus
    position_state: PositionState
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: float
    created_at: datetime
    updated_at: datetime
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OrdersListRequest(BaseModel):
    """Orders list request schema"""
    bot_id: str
    limit: int = Field(default=50, ge=1, le=200, description="Number of orders to fetch")
    status: Optional[OrderStatus] = Field(default=None, description="Filter by order status")
    position_state: Optional[PositionState] = Field(default=None, description="Filter by position state")
    start_date: Optional[datetime] = Field(default=None, description="Filter by start date")
    end_date: Optional[datetime] = Field(default=None, description="Filter by end date")


class OrdersResponse(BaseModel):
    """Orders list response schema"""
    orders: List[OrderResponse]
    total: int
    bot_id: str
    filters_applied: Dict[str, Any]


class OrderStats(BaseModel):
    """Order statistics"""
    total_orders: int
    open_orders: int
    closed_orders: int
    cancelled_orders: int
    total_pnl: float
    avg_pnl: float
    win_rate: float  # Percentage of profitable orders
    best_trade: Optional[float] = None
    worst_trade: Optional[float] = None
    total_fees: float = 0.0  # For future use with real trading


class OrdersStatsResponse(BaseModel):
    """Orders statistics response schema"""
    bot_id: str
    stats: OrderStats
    generated_at: datetime


class PortfolioSummary(BaseModel):
    """Portfolio summary for paper trading"""
    balance: float
    total_pnl: float
    open_positions_value: float
    total_value: float
    pnl_percentage: float
    available_balance: float
    margin_used: float = 0.0  # For future use


class PortfolioResponse(BaseModel):
    """Portfolio response schema"""
    bot_id: str
    summary: PortfolioSummary
    generated_at: datetime