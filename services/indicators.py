"""
Technical indicators service for calculating various trading indicators
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from core.logging import logger
from core.errors import InsufficientDataError, StrategyError
from models.candle import MarketCandle
from models.indicator import IndicatorSnapshot, IndicatorType


class IndicatorsService:
    """Service for calculating technical indicators"""
    
    def calc_support_resistance(
        self, 
        candles: List[MarketCandle], 
        window: int = 20,
        min_touches: int = 2
    ) -> Dict[str, Any]:
        """
        Calculate support and resistance levels
        
        Args:
            candles: List of market candles
            window: Lookback window for pivot points
            min_touches: Minimum touches required for level
            
        Returns:
            Dictionary with supports and resistances
        """
        if len(candles) < window * 2:
            raise InsufficientDataError(f"Need at least {window * 2} candles, got {len(candles)}")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame([{
            'timestamp': c.timestamp,
            'open': float(c.open),
            'high': float(c.high),
            'low': float(c.low),
            'close': float(c.close),
            'volume': float(c.volume)
        } for c in candles])
        
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate pivot points
        pivots = self._find_pivot_points(df, window)
        
        # Find support and resistance levels
        supports, resistances = self._identify_levels(df, pivots, min_touches)
        
        # Calculate strength for each level
        supports_with_strength = [
            {"price": level["price"], "strength": self._calculate_level_strength(df, level["price"], "support")}
            for level in supports
        ]
        
        resistances_with_strength = [
            {"price": level["price"], "strength": self._calculate_level_strength(df, level["price"], "resistance")}
            for level in resistances
        ]
        
        # Sort by strength
        supports_with_strength.sort(key=lambda x: x["strength"], reverse=True)
        resistances_with_strength.sort(key=lambda x: x["strength"], reverse=True)
        
        result = {
            "supports": supports_with_strength[:5],  # Top 5
            "resistances": resistances_with_strength[:5],  # Top 5
            "window": window,
            "min_touches": min_touches,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        logger.debug(
            f"Calculated support/resistance with {len(supports_with_strength)} supports and {len(resistances_with_strength)} resistances",
            supports=len(supports_with_strength),
            resistances=len(resistances_with_strength)
        )
        
        return result
    
    def calc_linear_regression_trend(
        self, 
        candles: List[MarketCandle], 
        window: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate linear regression trend
        
        Args:
            candles: List of market candles
            window: Lookback window
            
        Returns:
            Dictionary with slope, intercept, r2, and trend points
        """
        if len(candles) < window:
            raise InsufficientDataError(f"Need at least {window} candles, got {len(candles)}")
        
        # Get recent candles
        recent_candles = candles[-window:]
        
        # Prepare data
        prices = np.array([float(c.close) for c in recent_candles])
        x = np.arange(len(prices))
        
        # Calculate linear regression
        slope, intercept = np.polyfit(x, prices, 1)
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((prices - y_pred) ** 2)
        ss_tot = np.sum((prices - np.mean(prices)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Create trend points
        trend_points = [
            {"x": i, "y": float(slope * i + intercept)}
            for i in range(len(prices))
        ]
        
        result = {
            "slope": float(slope),
            "intercept": float(intercept),
            "r2": float(r2),
            "points": trend_points,
            "window": window,
            "trend_direction": "bullish" if slope > 0 else "bearish" if slope < 0 else "sideways",
            "trend_strength": abs(float(slope)),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        logger.debug(
            f"Calculated linear regression: slope={slope:.6f}, r2={r2:.3f}",
            slope=slope,
            r2=r2,
            trend_direction=result["trend_direction"]
        )
        
        return result
    
    def calc_volatility(
        self, 
        candles: List[MarketCandle], 
        window: int = 20
    ) -> Dict[str, Any]:
        """
        Calculate volatility indicators (standard deviation and ATR)
        
        Args:
            candles: List of market candles
            window: Lookback window
            
        Returns:
            Dictionary with volatility metrics
        """
        if len(candles) < window:
            raise InsufficientDataError(f"Need at least {window} candles, got {len(candles)}")
        
        recent_candles = candles[-window:]
        
        # Calculate returns
        closes = np.array([float(c.close) for c in recent_candles])
        returns = np.diff(closes) / closes[:-1]
        
        # Standard deviation of returns
        stdev = float(np.std(returns))
        
        # Average True Range (ATR)
        atr = self._calculate_atr(recent_candles)
        
        # Price volatility (coefficient of variation)
        mean_price = float(np.mean(closes))
        price_stdev = float(np.std(closes))
        cv = price_stdev / mean_price if mean_price != 0 else 0
        
        result = {
            "stdev": stdev,
            "atr": atr,
            "price_volatility": cv,
            "window": window,
            "mean_price": mean_price,
            "price_range": float(np.max(closes) - np.min(closes)),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        logger.debug(
            f"Calculated volatility: stdev={stdev:.6f}, atr={atr:.2f}",
            stdev=stdev,
            atr=atr
        )
        
        return result
    
    async def save_indicator_snapshot(
        self,
        db: Session,
        bot_id: str,
        timestamp: datetime,
        indicator_type: str,
        value: Dict[str, Any]
    ) -> IndicatorSnapshot:
        """Save indicator snapshot to database"""
        snapshot = IndicatorSnapshot.create(
            bot_id=bot_id,
            timestamp=timestamp,
            indicator_type=indicator_type,
            value=value
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        logger.debug(
            f"Saved indicator snapshot: {indicator_type}",
            bot_id=bot_id,
            indicator_type=indicator_type,
            timestamp=timestamp.isoformat()
        )
        
        return snapshot
    
    async def compute_and_store_indicators(
        self,
        db: Session,
        bot_id: str,
        candles: List[MarketCandle],
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Compute all indicators and store snapshots
        
        Args:
            db: Database session
            bot_id: Bot ID
            candles: List of market candles
            timestamp: Current timestamp
            
        Returns:
            Dictionary with computed indicators
        """
        indicators = {}
        
        try:
            # Support and Resistance
            sr_indicators = self.calc_support_resistance(candles)
            await self.save_indicator_snapshot(
                db, bot_id, timestamp, IndicatorType.SUPPORT_RESISTANCE, sr_indicators
            )
            indicators[IndicatorType.SUPPORT_RESISTANCE] = sr_indicators
            
            # Linear Regression
            regression_indicators = self.calc_linear_regression_trend(candles)
            await self.save_indicator_snapshot(
                db, bot_id, timestamp, IndicatorType.LINEAR_REGRESSION, regression_indicators
            )
            indicators[IndicatorType.LINEAR_REGRESSION] = regression_indicators
            
            # Volatility
            volatility_indicators = self.calc_volatility(candles)
            await self.save_indicator_snapshot(
                db, bot_id, timestamp, IndicatorType.VOLATILITY, volatility_indicators
            )
            indicators[IndicatorType.VOLATILITY] = volatility_indicators
            
            logger.info(
                f"Computed and stored indicators for bot {bot_id}",
                bot_id=bot_id,
                indicators_count=len(indicators),
                timestamp=timestamp.isoformat()
            )
            
        except Exception as e:
            logger.error(
                f"Failed to compute indicators for bot {bot_id}",
                bot_id=bot_id,
                error=str(e)
            )
            raise StrategyError(f"Failed to compute indicators: {str(e)}")
        
        return indicators
    
    def get_latest_indicators(
        self,
        db: Session,
        bot_id: str,
        limit: int = 50,
        indicator_type: Optional[str] = None
    ) -> List[IndicatorSnapshot]:
        """Get latest indicator snapshots"""
        query = db.query(IndicatorSnapshot).filter(
            IndicatorSnapshot.bot_id == bot_id
        )
        
        if indicator_type:
            query = query.filter(IndicatorSnapshot.indicator_type == indicator_type)
        
        indicators = query.order_by(desc(IndicatorSnapshot.timestamp)).limit(limit).all()
        
        return indicators
    
    def _find_pivot_points(self, df: pd.DataFrame, window: int) -> List[Dict]:
        """Find pivot points (highs and lows)"""
        pivots = []
        
        for i in range(window, len(df) - window):
            # Check for pivot high
            high_window = df.iloc[i-window:i+window+1]
            if df.iloc[i]['high'] == high_window['high'].max():
                pivots.append({
                    'index': i,
                    'timestamp': df.iloc[i]['timestamp'],
                    'type': 'high',
                    'price': float(df.iloc[i]['high'])
                })
            
            # Check for pivot low
            if df.iloc[i]['low'] == low_window['low'].min():
                pivots.append({
                    'index': i,
                    'timestamp': df.iloc[i]['timestamp'],
                    'type': 'low',
                    'price': float(df.iloc[i]['low'])
                })
        
        return pivots
    
    def _identify_levels(
        self, 
        df: pd.DataFrame, 
        pivots: List[Dict], 
        min_touches: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """Identify support and resistance levels from pivot points"""
        prices = [p['price'] for p in pivots]
        
        # Group similar prices
        tolerance = np.std(prices) * 0.01  # 1% tolerance
        levels = []
        
        for pivot in pivots:
            price = pivot['price']
            touches = 1
            
            # Find touches within tolerance
            for existing in levels:
                if abs(existing['price'] - price) <= tolerance:
                    existing['touches'] += 1
                    existing['pivots'].append(pivot)
                    break
            else:
                levels.append({
                    'price': price,
                    'touches': 1,
                    'pivots': [pivot],
                    'type': 'resistance' if pivot['type'] == 'high' else 'support'
                })
        
        # Filter by minimum touches
        valid_levels = [l for l in levels if l['touches'] >= min_touches]
        
        # Separate supports and resistances
        supports = [l for l in valid_levels if l['type'] == 'support']
        resistances = [l for l in valid_levels if l['type'] == 'resistance']
        
        return supports, resistances
    
    def _calculate_level_strength(
        self, 
        df: pd.DataFrame, 
        level_price: float, 
        level_type: str
    ) -> float:
        """Calculate strength of support/resistance level"""
        tolerance = level_price * 0.005  # 0.5% tolerance
        
        if level_type == "support":
            # Count how many times price bounced off this support
            touches = 0
            for i in range(1, len(df)):
                if (df.iloc[i-1]['close'] > level_price and 
                    df.iloc[i]['close'] <= level_price + tolerance and
                    df.iloc[i]['low'] <= level_price):
                    touches += 1
        else:  # resistance
            # Count how many times price was rejected at this resistance
            touches = 0
            for i in range(1, len(df)):
                if (df.iloc[i-1]['close'] < level_price and 
                    df.iloc[i]['close'] >= level_price - tolerance and
                    df.iloc[i]['high'] >= level_price):
                    touches += 1
        
        # Strength based on touches and volume
        total_volume = df['volume'].sum()
        level_volume = sum([
            df.iloc[i]['volume'] for i in range(len(df))
            if abs(df.iloc[i]['close'] - level_price) <= tolerance
        ])
        
        volume_ratio = level_volume / total_volume if total_volume > 0 else 0
        
        return min(1.0, (touches * 0.3) + (volume_ratio * 0.7))
    
    def _calculate_atr(self, candles: List[MarketCandle], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(candles) < period + 1:
            return 0.0
        
        true_ranges = []
        
        for i in range(1, len(candles)):
            current = candles[i]
            previous = candles[i-1]
            
            tr1 = float(current.high - current.low)
            tr2 = abs(float(current.high - previous.close))
            tr3 = abs(float(current.low - previous.close))
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        return float(np.mean(true_ranges[-period:]))


# Global indicators service instance
indicators_service = IndicatorsService()