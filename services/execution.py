"""
Paper trading execution service for simulated order execution
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.logging import logger, log_order_execution
from core.errors import ExecutionError, PositionError
from models.bot import Bot
from models.order import Order, OrderSide, OrderStatus, PositionState
from models.signal import Signal
from services.strategies.base import StrategyResult


class ExecutionService:
    """Service for paper trading execution"""
    
    def __init__(self, default_balance: float = 10000.0):
        self.default_balance = default_balance
    
    def get_open_position(
        self,
        db: Session,
        bot_id: str
    ) -> Optional[Order]:
        """
        Get open position for bot
        
        Args:
            db: Database session
            bot_id: Bot ID
            
        Returns:
            Open Order or None
        """
        open_order = db.query(Order).filter(
            and_(
                Order.bot_id == bot_id,
                Order.status == OrderStatus.OPEN.value
            )
        ).first()
        
        return open_order
    
    def open_paper_position(
        self,
        db: Session,
        bot: Bot,
        signal: Signal,
        price: float,
        quantity: float
    ) -> Order:
        """
        Open a paper trading position
        
        Args:
            db: Database session
            bot: Bot instance
            signal: Signal that triggered the order
            price: Entry price
            quantity: Position quantity
            
        Returns:
            Created Order
        """
        # Check if position already exists
        existing_position = self.get_open_position(db, bot.id)
        if existing_position:
            raise PositionError(
                f"Position already exists for bot {bot.id}",
                {"existing_order_id": existing_position.id}
            )
        
        # Create buy order
        order = Order.create(
            bot_id=bot.id,
            side=OrderSide.BUY,
            quantity=quantity,
            price=price,
            signal_id=signal.id,
            meta={
                "strategy": bot.strategy_id.value,
                "symbol": bot.symbol,
                "timeframe": bot.timeframe,
                "signal_confidence": float(signal.confidence),
                "signal_reason": signal.reason
            }
        )
        
        # Set position state
        order.position_state = PositionState.LONG.value
        order.entry_price = price
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(
            f"Opened paper position for bot {bot.id}",
            bot_id=bot.id,
            order_id=order.id,
            symbol=bot.symbol,
            side="BUY",
            quantity=quantity,
            price=price
        )
        
        log_order_execution(
            bot_id=bot.id,
            action="opened",
            order_id=order.id,
            price=price,
            quantity=quantity
        )
        
        return order
    
    def close_paper_position(
        self,
        db: Session,
        bot: Bot,
        signal: Signal,
        price: float,
        reason: str = "Signal-based exit"
    ) -> Order:
        """
        Close existing paper trading position
        
        Args:
            db: Database session
            bot: Bot instance
            signal: Signal that triggered the close
            price: Exit price
            reason: Reason for closing
            
        Returns:
            Updated Order
        """
        # Get open position
        open_order = self.get_open_position(db, bot.id)
        if not open_order:
            raise PositionError(
                f"No open position to close for bot {bot.id}",
                {"bot_id": bot.id}
            )
        
        if not open_order.is_buy_order():
            raise PositionError(
                f"Cannot close non-buy position",
                {"order_id": open_order.id, "side": open_order.side}
            )
        
        # Calculate P&L
        entry_price = float(open_order.entry_price)
        quantity = float(open_order.quantity)
        pnl = (price - entry_price) * quantity
        
        # Create sell order
        sell_order = Order.create(
            bot_id=bot.id,
            side=OrderSide.SELL,
            quantity=quantity,
            price=price,
            signal_id=signal.id,
            meta={
                "strategy": bot.strategy_id.value,
                "symbol": bot.symbol,
                "timeframe": bot.timeframe,
                "signal_confidence": float(signal.confidence),
                "signal_reason": signal.reason,
                "exit_reason": reason,
                "entry_order_id": open_order.id
            }
        )
        
        # Close the position
        sell_order.position_state = PositionState.NONE.value
        sell_order.entry_price = entry_price
        sell_order.exit_price = price
        sell_order.pnl = pnl
        sell_order.status = OrderStatus.CLOSED.value
        
        # Update original order
        open_order.status = OrderStatus.CLOSED.value
        open_order.exit_price = price
        open_order.pnl = pnl
        
        db.add(sell_order)
        db.commit()
        db.refresh(sell_order)
        
        logger.info(
            f"Closed paper position for bot {bot.id}",
            bot_id=bot.id,
            entry_order_id=open_order.id,
            exit_order_id=sell_order.id,
            symbol=bot.symbol,
            side="SELL",
            quantity=quantity,
            entry_price=entry_price,
            exit_price=price,
            pnl=pnl,
            reason=reason
        )
        
        log_order_execution(
            bot_id=bot.id,
            action="closed",
            order_id=sell_order.id,
            price=price,
            quantity=quantity
        )
        
        return sell_order
    
    def execute_signal(
        self,
        db: Session,
        bot: Bot,
        signal_result: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        Execute trading signal (paper trading)
        
        Args:
            db: Database session
            bot: Bot instance
            signal_result: Strategy evaluation result
            current_price: Current market price
            
        Returns:
            Dictionary with execution result
        """
        signal_type = signal_result["signal_type"]
        confidence = signal_result["confidence"]
        
        # Get current position
        open_position = self.get_open_position(db, bot.id)
        has_position = open_position is not None
        
        result = {
            "action": "none",
            "signal_type": signal_type,
            "confidence": confidence,
            "reason": signal_result["reason"],
            "current_price": current_price,
            "has_position": has_position,
            "order_id": None,
            "pnl": 0.0
        }
        
        try:
            if signal_type == "BUY":
                if has_position:
                    # Already in position, don't buy more
                    result["action"] = "ignored"
                    result["reason"] = "Already in position"
                    logger.info(
                        f"BUY signal ignored - already in position",
                        bot_id=bot.id,
                        current_position_id=open_position.id
                    )
                else:
                    # Open new position
                    quantity = self._calculate_position_size(bot, current_price, confidence)
                    order = self._create_signal(db, bot, signal_result, "BUY")
                    
                    position = self.open_paper_position(
                        db=db,
                        bot=bot,
                        signal=order,
                        price=current_price,
                        quantity=quantity
                    )
                    
                    result.update({
                        "action": "opened",
                        "order_id": position.id,
                        "quantity": quantity,
                        "entry_price": current_price
                    })
            
            elif signal_type == "SELL":
                if not has_position:
                    # No position to sell
                    result["action"] = "ignored"
                    result["reason"] = "No position to close"
                    logger.info(
                        f"SELL signal ignored - no open position",
                        bot_id=bot.id
                    )
                else:
                    # Close position
                    order = self._create_signal(db, bot, signal_result, "SELL")
                    
                    position = self.close_paper_position(
                        db=db,
                        bot=bot,
                        signal=order,
                        price=current_price,
                        reason="SELL signal"
                    )
                    
                    result.update({
                        "action": "closed",
                        "order_id": position.id,
                        "quantity": float(position.quantity),
                        "exit_price": current_price,
                        "pnl": float(position.pnl)
                    })
            
            else:  # HOLD
                result["action"] = "hold"
                result["reason"] = "Hold signal - no action taken"
                
                if has_position:
                    # Check if we should close due to stop loss or take profit
                    stop_result = self._check_exit_conditions(
                        db=db,
                        bot=bot,
                        position=open_position,
                        current_price=current_price,
                        confidence=confidence
                    )
                    
                    if stop_result["should_exit"]:
                        # Close position
                        order = self._create_signal(db, bot, signal_result, "SELL")
                        
                        position = self.close_paper_position(
                            db=db,
                            bot=bot,
                            signal=order,
                            price=current_price,
                            reason=stop_result["reason"]
                        )
                        
                        result.update({
                            "action": "stopped",
                            "order_id": position.id,
                            "exit_price": current_price,
                            "pnl": float(position.pnl),
                            "stop_reason": stop_result["reason"]
                        })
        
        except Exception as e:
            logger.error(
                f"Error executing signal for bot {bot.id}",
                bot_id=bot.id,
                signal_type=signal_type,
                error=str(e)
            )
            raise ExecutionError(f"Failed to execute signal: {str(e)}")
        
        return result
    
    def get_portfolio_summary(
        self,
        db: Session,
        bot_id: str
    ) -> Dict[str, Any]:
        """
        Get portfolio summary for bot
        
        Args:
            db: Database session
            bot_id: Bot ID
            
        Returns:
            Portfolio summary dictionary
        """
        # Get all orders
        orders = db.query(Order).filter(Order.bot_id == bot_id).all()
        
        # Calculate statistics
        total_orders = len(orders)
        open_orders = [o for o in orders if o.is_open()]
        closed_orders = [o for o in orders if o.is_closed()]
        
        total_pnl = sum(float(o.pnl) for o in closed_orders)
        open_pnl = sum(float(o.pnl) for o in open_orders)
        
        # Calculate win rate
        profitable_trades = [o for o in closed_orders if float(o.pnl) > 0]
        win_rate = len(profitable_trades) / len(closed_orders) * 100 if closed_orders else 0
        
        # Best and worst trades
        pnls = [float(o.pnl) for o in closed_orders if float(o.pnl) != 0]
        best_trade = max(pnls) if pnls else None
        worst_trade = min(pnls) if pnls else None
        
        # Current position value
        open_position = self.get_open_position(db, bot_id)
        open_positions_value = 0.0
        if open_position:
            # Assume we can sell at current market price for paper trading
            # In real trading, this would need current market price
            open_positions_value = float(open_position.quantity) * 1000  # Placeholder
        
        # Available balance (paper trading balance)
        available_balance = self.default_balance + total_pnl + open_pnl
        total_value = available_balance + open_positions_value
        
        # P&L percentage
        pnl_percentage = (total_pnl / self.default_balance) * 100 if self.default_balance > 0 else 0
        
        return {
            "balance": self.default_balance,
            "available_balance": available_balance,
            "total_pnl": total_pnl,
            "open_positions_value": open_positions_value,
            "total_value": total_value,
            "pnl_percentage": pnl_percentage,
            "total_orders": total_orders,
            "open_orders": len(open_orders),
            "closed_orders": len(closed_orders),
            "win_rate": win_rate,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "has_open_position": open_position is not None
        }
    
    def _calculate_position_size(
        self,
        bot: Bot,
        price: float,
        confidence: float
    ) -> float:
        """Calculate position size based on confidence and risk management"""
        # Simple position sizing: risk 2% of paper balance per trade
        base_risk = 0.02  # 2%
        confidence_multiplier = confidence  # Scale by confidence
        
        risk_amount = self.default_balance * base_risk * confidence_multiplier
        quantity = risk_amount / price
        
        # Minimum and maximum position sizes
        min_quantity = 0.001  # Minimum $1 position
        max_quantity = self.default_balance * 0.1 / price  # Max 10% of balance
        
        return max(min_quantity, min(quantity, max_quantity))
    
    def _create_signal(
        self,
        db: Session,
        bot: Bot,
        signal_result: Dict[str, Any],
        side: str
    ) -> Signal:
        """Create signal record for order execution"""
        signal = Signal.create(
            bot_id=bot.id,
            timestamp=datetime.utcnow(),
            signal_type=signal_result["signal_type"],
            confidence=signal_result["confidence"],
            reason=signal_result["reason"],
            meta=signal_result.get("metadata", {})
        )
        
        db.add(signal)
        db.commit()
        db.refresh(signal)
        
        return signal
    
    def _check_exit_conditions(
        self,
        db: Session,
        bot: Bot,
        position: Order,
        current_price: float,
        confidence: float
    ) -> Dict[str, Any]:
        """Check if position should be exited based on stop loss/take profit"""
        # This is a simplified implementation
        # In a real system, you'd have configurable stop loss/take profit levels
        
        entry_price = float(position.entry_price)
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Stop loss: 5% loss
        if pnl_pct <= -5.0:
            return {
                "should_exit": True,
                "reason": f"Stop loss triggered: {pnl_pct:.2f}%"
            }
        
        # Take profit: 15% gain
        if pnl_pct >= 15.0:
            return {
                "should_exit": True,
                "reason": f"Take profit triggered: {pnl_pct:.2f}%"
            }
        
        # Time-based exit (if position held for more than 24 hours)
        hours_held = (datetime.utcnow() - position.created_at).total_seconds() / 3600
        if hours_held >= 24 and confidence < 0.3:
            return {
                "should_exit": True,
                "reason": f"Time-based exit: {hours_held:.1f} hours held, low confidence"
            }
        
        return {
            "should_exit": False,
            "reason": "No exit conditions met"
        }


# Global execution service instance
execution_service = ExecutionService()