"""
Blue Sky Strategy - MVP trading strategy

A breakout strategy that buys when current close price exceeds
the maximum high of the previous N candles.
"""
from typing import List, Dict, Any
from datetime import datetime

from models.candle import MarketCandle
from models.signal import SignalType
from services.strategies.base import BaseStrategy, create_hold_signal, create_buy_signal


class BlueSkyStrategy(BaseStrategy):
    """Blue Sky breakout strategy implementation"""
    
    @property
    def strategy_id(self) -> str:
        return "blue_sky"
    
    @property
    def name(self) -> str:
        return "Blue Sky"
    
    @property
    def description(self) -> str:
        return """Breakout strategy that buys when current close price 
        exceeds the maximum high of the previous N candles. 
        Ideal for trending markets with clear breakouts."""
    
    def evaluate(
        self,
        candles: List[MarketCandle],
        indicators: Dict[str, Any],
        params: Dict[str, Any]
    ) -> "StrategyResult":
        """
        Evaluate market data using Blue Sky strategy
        
        Rule: If close_now > max(high[-N:]) → BUY else HOLD
        
        Args:
            candles: Historical market candles
            indicators: Technical indicators (not used in this strategy)
            params: Strategy parameters
            
        Returns:
            StrategyResult with signal_type, confidence, reason, metadata
        """
        # Get parameters
        lookback = params.get("lookback", 20)
        min_confidence = params.get("min_confidence", 0.6)
        
        # Check if we have enough data
        required_data = self.get_required_data_points(params)
        if len(candles) < required_data:
            return create_hold_signal(
                f"Insufficient data: need {required_data}, have {len(candles)}"
            )
        
        # Get current and previous candles
        current_candle = candles[-1]
        previous_candles = candles[-(lookback + 1):-1]  # Exclude current
        
        if not previous_candles:
            return create_hold_signal("No previous candles for comparison")
        
        # Calculate maximum high of previous N candles
        max_prev_high = max(float(c.high) for c in previous_candles)
        close_now = float(current_candle.close)
        
        # Check for breakout
        breakout_threshold = max_prev_high * 1.001  # 0.1% above max high
        is_breakout = close_now > max_prev_high
        
        # Calculate confidence based on breakout strength
        if is_breakout:
            breakout_pct = (close_now - max_prev_high) / max_prev_high
            
            # Use volatility to normalize confidence
            volatility = indicators.get("volatility", {}).get("stdev", 0.001)
            volatility_normalized = breakout_pct / max(volatility, 0.0001)
            
            # Base confidence on breakout strength
            confidence = min(0.95, 0.5 + (breakout_pct * 100))  # Scale up
            
            # Adjust by volatility (higher volatility = lower confidence)
            confidence = confidence * (1 / (1 + volatility_normalized))
            
            # Ensure minimum confidence threshold
            if confidence >= min_confidence:
                metadata = {
                    "lookback": lookback,
                    "max_prev_high": max_prev_high,
                    "close_now": close_now,
                    "breakout_pct": breakout_pct,
                    "breakout_threshold": breakout_threshold,
                    "volatility": volatility,
                    "confidence_components": {
                        "base_confidence": 0.5 + (breakout_pct * 100),
                        "volatility_adjustment": 1 / (1 + volatility_normalized),
                        "final_confidence": confidence
                    }
                }
                
                return create_buy_signal(
                    f"Blue Sky breakout: {close_now:.2f} > {max_prev_high:.2f} ({(breakout_pct*100):.2f}% above max high)",
                    confidence,
                    metadata
                )
            else:
                return create_hold_signal(
                    f"Breakout detected but confidence {confidence:.3f} below threshold {min_confidence}"
                )
        else:
            # No breakout, hold signal
            gap = (max_prev_high - close_now) / close_now
            return create_hold_signal(
                f"No breakout: {close_now:.2f} < {max_prev_high:.2f} ({gap:.2%} below max high)",
                confidence=max(0.1, 1.0 - abs(gap))  # Higher confidence when far from breakout
            )
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate Blue Sky strategy parameters"""
        try:
            lookback = params.get("lookback", 20)
            min_confidence = params.get("min_confidence", 0.6)
            
            # Validate lookback
            if not isinstance(lookback, int) or lookback < 5 or lookback > 100:
                return False
            
            # Validate confidence
            if not isinstance(min_confidence, (int, float)) or min_confidence < 0.1 or min_confidence > 1.0:
                return False
            
            return True
        except (TypeError, KeyError):
            return False
    
    def get_required_data_points(self, params: Dict[str, Any]) -> int:
        """Get minimum required data points for Blue Sky strategy"""
        lookback = params.get("lookback", 20)
        return lookback + 1  # Current candle + previous N candles
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information"""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "description": self.description,
            "parameters": {
                "lookback": {
                    "type": "int",
                    "default": 20,
                    "min": 5,
                    "max": 100,
                    "description": "Number of previous candles to check for breakout"
                },
                "min_confidence": {
                    "type": "float",
                    "default": 0.6,
                    "min": 0.1,
                    "max": 1.0,
                    "description": "Minimum confidence threshold for buy signals"
                }
            },
            "signal_types": ["BUY", "HOLD"],
            "data_requirements": {
                "candles": "lookback + 1",
                "indicators": ["volatility"]  # Optional but recommended
            },
            "best_market_conditions": [
                "Trending markets",
                "Clear breakout patterns",
                "Low to medium volatility"
            ],
            "risk_factors": [
                "False breakouts in choppy markets",
                "High volatility can reduce confidence",
                "Requires sufficient historical data"
            ]
        }


# Create global strategy instance
blue_sky_strategy = BlueSkyStrategy()