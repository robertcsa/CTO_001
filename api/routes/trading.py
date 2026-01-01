"""
Trading signals and orders API routes
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from core.db import get_db
from api.deps import get_current_active_user, get_bot_or_404
from schemas.signal import (
    SignalsListRequest, SignalsResponse, SignalResponse,
    SignalsStatsResponse, SignalStats
)
from schemas.order import (
    OrdersListRequest, OrdersResponse, OrderResponse,
    OrdersStatsResponse, OrderStats, PortfolioResponse, PortfolioSummary
)
from models.bot import Bot
from models.signal import Signal, SignalType
from models.order import Order, OrderStatus, PositionState
from models.user import User
from services.audit import get_signal_history, get_signal_statistics
from services.execution import execution_service


router = APIRouter(prefix="/trading", tags=["trading"])


# Signals endpoints
@router.get("/signals", response_model=SignalsResponse)
async def get_signals(
    bot_id: str = Query(..., description="Bot ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of signals"),
    signal_type: Optional[SignalType] = Query(None, description="Filter by signal type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get trading signals for bot
    """
    try:
        # Verify bot ownership
        bot = db.query(Bot).filter(
            Bot.id == bot_id,
            Bot.user_id == current_user.id
        ).first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found or access denied"
            )
        
        signals = get_signal_history(
            db=db,
            bot_id=bot_id,
            limit=limit,
            signal_type=signal_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return SignalsResponse(
            signals=[SignalResponse.from_orm(signal) for signal in signals],
            total=len(signals),
            bot_id=bot_id,
            filters_applied={
                "signal_type": signal_type.value if signal_type else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signals: {str(e)}"
        )


@router.get("/signals/stats/{bot_id}", response_model=SignalsStatsResponse)
async def get_signal_stats(
    bot_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get signal statistics for bot
    """
    try:
        stats = get_signal_statistics(db=db, bot_id=bot_id, days=days)
        
        return SignalsStatsResponse(
            bot_id=bot_id,
            stats=SignalStats(**stats),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signal stats: {str(e)}"
        )


@router.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific signal by ID
    """
    try:
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found"
            )
        
        # Verify bot ownership
        bot = db.query(Bot).filter(
            Bot.id == signal.bot_id,
            Bot.user_id == current_user.id
        ).first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return SignalResponse.from_orm(signal)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signal: {str(e)}"
        )


# Orders endpoints
@router.get("/orders", response_model=OrdersResponse)
async def get_orders(
    bot_id: str = Query(..., description="Bot ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of orders"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    position_state: Optional[PositionState] = Query(None, description="Filter by position state"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get orders for bot
    """
    try:
        # Verify bot ownership
        bot = db.query(Bot).filter(
            Bot.id == bot_id,
            Bot.user_id == current_user.id
        ).first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found or access denied"
            )
        
        # Build query
        query = db.query(Order).filter(Order.bot_id == bot_id)
        
        if status:
            query = query.filter(Order.status == status.value)
        
        if position_state:
            query = query.filter(Order.position_state == position_state.value)
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        
        orders = query.order_by(Order.created_at.desc()).limit(limit).all()
        
        return OrdersResponse(
            orders=[OrderResponse.from_orm(order) for order in orders],
            total=len(orders),
            bot_id=bot_id,
            filters_applied={
                "status": status.value if status else None,
                "position_state": position_state.value if position_state else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}"
        )


@router.get("/orders/stats/{bot_id}", response_model=OrdersStatsResponse)
async def get_order_stats(
    bot_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get order statistics for bot
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        orders = db.query(Order).filter(
            Order.bot_id == bot_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).all()
        
        # Calculate statistics
        total_orders = len(orders)
        open_orders = len([o for o in orders if o.is_open()])
        closed_orders = len([o for o in orders if o.is_closed()])
        cancelled_orders = len([o for o in orders if o.is_cancelled()])
        
        # P&L calculations
        total_pnl = sum(float(o.pnl) for o in closed_orders)
        avg_pnl = total_pnl / len(closed_orders) if closed_orders else 0.0
        
        # Win rate
        profitable_trades = [o for o in closed_orders if float(o.pnl) > 0]
        win_rate = (len(profitable_trades) / len(closed_orders) * 100) if closed_orders else 0.0
        
        # Best and worst trades
        pnls = [float(o.pnl) for o in closed_orders if float(o.pnl) != 0]
        best_trade = max(pnls) if pnls else None
        worst_trade = min(pnls) if pnls else None
        
        stats = OrderStats(
            total_orders=total_orders,
            open_orders=open_orders,
            closed_orders=closed_orders,
            cancelled_orders=cancelled_orders,
            total_pnl=total_pnl,
            avg_pnl=avg_pnl,
            win_rate=win_rate,
            best_trade=best_trade,
            worst_trade=worst_trade,
            total_fees=0.0  # Paper trading, no fees
        )
        
        return OrdersStatsResponse(
            bot_id=bot_id,
            stats=stats,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order stats: {str(e)}"
        )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific order by ID
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Verify bot ownership
        bot = db.query(Bot).filter(
            Bot.id == order.bot_id,
            Bot.user_id == current_user.id
        ).first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return OrderResponse.from_orm(order)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}"
        )


@router.get("/portfolio/{bot_id}", response_model=PortfolioResponse)
async def get_portfolio_summary(
    bot_id: str,
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get portfolio summary for bot (paper trading)
    """
    try:
        portfolio_data = execution_service.get_portfolio_summary(db=db, bot_id=bot_id)
        
        summary = PortfolioSummary(**portfolio_data)
        
        return PortfolioResponse(
            bot_id=bot_id,
            summary=summary,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio summary: {str(e)}"
        )


@router.get("/position/{bot_id}")
async def get_current_position(
    bot_id: str,
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current open position for bot
    """
    try:
        open_position = execution_service.get_open_position(db=db, bot_id=bot_id)
        
        if open_position:
            return {
                "has_position": True,
                "position": OrderResponse.from_orm(open_position),
                "unrealized_pnl": float(open_position.pnl)
            }
        else:
            return {
                "has_position": False,
                "position": None,
                "unrealized_pnl": 0.0
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get position: {str(e)}"
        )


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel open order
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Verify bot ownership
        bot = db.query(Bot).filter(
            Bot.id == order.bot_id,
            Bot.user_id == current_user.id
        ).first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if not order.is_open():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only open orders can be cancelled"
            )
        
        # Cancel order
        order.status = OrderStatus.CANCELLED.value
        db.commit()
        
        return {
            "message": "Order cancelled successfully",
            "order_id": order_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.get("/summary/{bot_id}")
async def get_trading_summary(
    bot_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive trading summary for bot
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get signals and orders
        signals = get_signal_history(db=db, bot_id=bot_id, limit=1000, 
                                   start_date=start_date, end_date=end_date)
        orders = db.query(Order).filter(
            Order.bot_id == bot_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).all()
        
        # Get current position
        open_position = execution_service.get_open_position(db=db, bot_id=bot_id)
        
        # Calculate summary
        total_signals = len(signals)
        buy_signals = len([s for s in signals if s.is_buy_signal])
        sell_signals = len([s for s in signals if s.is_sell_signal])
        hold_signals = len([s for s in signals if s.is_hold_signal])
        
        closed_orders = [o for o in orders if o.is_closed()]
        total_pnl = sum(float(o.pnl) for o in closed_orders)
        win_rate = len([o for o in closed_orders if float(o.pnl) > 0]) / len(closed_orders) * 100 if closed_orders else 0
        
        return {
            "bot_id": bot_id,
            "period_days": days,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "signals": {
                "total": total_signals,
                "buy": buy_signals,
                "sell": sell_signals,
                "hold": hold_signals,
                "buy_ratio": buy_signals / total_signals if total_signals > 0 else 0
            },
            "orders": {
                "total": len(orders),
                "open": len([o for o in orders if o.is_open()]),
                "closed": len(closed_orders),
                "cancelled": len([o for o in orders if o.is_cancelled()])
            },
            "performance": {
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "avg_pnl_per_trade": total_pnl / len(closed_orders) if closed_orders else 0
            },
            "position": {
                "has_open_position": open_position is not None,
                "unrealized_pnl": float(open_position.pnl) if open_position else 0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trading summary: {str(e)}"
        )