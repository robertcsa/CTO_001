"""
Market data service for fetching and managing candle data
"""
import asyncio
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from core.config import settings
from core.logging import logger
from core.errors import MarketDataError, RateLimitError, TimeoutError
from models.candle import MarketCandle


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self):
        """Acquire permission to make a request"""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        # Check if we can make a request
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        # Add current request
        self.requests.append(now)


class MarketDataService:
    """Service for market data operations"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(
            max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            time_window=60
        )
        self.client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def fetch_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = 100,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch candles from market data API
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            timeframe: Timeframe (e.g., 1h, 4h, 1d)
            limit: Number of candles to fetch
            end_time: End time for data fetching
            
        Returns:
            List of candle dictionaries
        """
        try:
            await self.rate_limiter.acquire()
            
            # Convert timeframe to API format
            api_timeframe = self._convert_timeframe(timeframe)
            
            # Prepare API parameters
            params = {
                "symbol": symbol.upper(),
                "interval": api_timeframe,
                "limit": min(limit, 1000)  # API limit
            }
            
            if end_time:
                params["endTime"] = int(end_time.timestamp() * 1000)
            
            # Make API request
            response = await self.client.get(
                f"{settings.MARKET_DATA_BASE_URL}/api/v3/klines",
                params=params
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Convert to our format
            candles = []
            for item in data:
                candle = {
                    "open_time": datetime.fromtimestamp(item[0] / 1000),
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5]),
                    "close_time": datetime.fromtimestamp(item[6] / 1000)
                }
                candles.append(candle)
            
            logger.debug(
                f"Fetched {len(candles)} candles for {symbol} {timeframe}",
                symbol=symbol,
                timeframe=timeframe,
                count=len(candles)
            )
            
            return candles
            
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timeout for {symbol} {timeframe}: {str(e)}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {symbol} {timeframe}")
            raise MarketDataError(f"API error for {symbol} {timeframe}: {str(e)}")
        except Exception as e:
            raise MarketDataError(f"Failed to fetch candles for {symbol} {timeframe}: {str(e)}")
    
    async def upsert_candles(
        self, 
        db: Session, 
        candles_data: List[Dict], 
        symbol: str, 
        timeframe: str
    ) -> int:
        """
        Insert or update candles in database (avoiding duplicates)
        
        Args:
            db: Database session
            candles_data: List of candle data dictionaries
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            Number of candles inserted/updated
        """
        inserted_count = 0
        
        for candle_data in candles_data:
            try:
                # Create candle instance
                candle = MarketCandle.create_from_dict(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=candle_data["open_time"],
                    data={
                        "open": candle_data["open"],
                        "high": candle_data["high"],
                        "low": candle_data["low"],
                        "close": candle_data["close"],
                        "volume": candle_data["volume"]
                    }
                )
                
                # Try to insert, ignore if duplicate
                db.add(candle)
                db.commit()
                inserted_count += 1
                
            except Exception as e:
                # Rollback and continue with next candle
                db.rollback()
                logger.debug(
                    f"Duplicate candle skipped: {symbol} {timeframe} {candle_data['open_time']}",
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=candle_data["open_time"].isoformat()
                )
                continue
        
        logger.info(
            f"Upserted {inserted_count} candles for {symbol} {timeframe}",
            symbol=symbol,
            timeframe=timeframe,
            count=inserted_count
        )
        
        return inserted_count
    
    def get_candles(
        self,
        db: Session,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MarketCandle]:
        """
        Get candles from database
        
        Args:
            db: Database session
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of candles to return
            
        Returns:
            List of MarketCandle objects
        """
        query = db.query(MarketCandle).filter(
            and_(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe
            )
        )
        
        if start_time:
            query = query.filter(MarketCandle.timestamp >= start_time)
        
        if end_time:
            query = query.filter(MarketCandle.timestamp <= end_time)
        
        query = query.order_by(desc(MarketCandle.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        candles = query.all()
        
        logger.debug(
            f"Retrieved {len(candles)} candles for {symbol} {timeframe}",
            symbol=symbol,
            timeframe=timeframe,
            count=len(candles)
        )
        
        return candles
    
    def get_latest_candle(
        self,
        db: Session,
        symbol: str,
        timeframe: str
    ) -> Optional[MarketCandle]:
        """
        Get the latest candle for symbol and timeframe
        
        Args:
            db: Database session
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            Latest MarketCandle or None
        """
        return db.query(MarketCandle).filter(
            and_(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe
            )
        ).order_by(desc(MarketCandle.timestamp)).first()
    
    def get_candle_count(
        self,
        db: Session,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Get count of candles in database
        
        Args:
            db: Database session
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Number of candles
        """
        query = db.query(MarketCandle).filter(
            and_(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe
            )
        )
        
        if start_time:
            query = query.filter(MarketCandle.timestamp >= start_time)
        
        if end_time:
            query = query.filter(MarketCandle.timestamp <= end_time)
        
        return query.count()
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to API format"""
        timeframe_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
            "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
        }
        
        if timeframe not in timeframe_map:
            raise MarketDataError(f"Unsupported timeframe: {timeframe}")
        
        return timeframe_map[timeframe]
    
    async def refresh_market_data(
        self,
        db: Session,
        symbol: str,
        timeframe: str,
        lookback_hours: int = 24
    ) -> Tuple[int, int]:
        """
        Refresh market data for symbol and timeframe
        
        Args:
            db: Database session
            symbol: Trading symbol
            timeframe: Timeframe
            lookback_hours: Hours to look back for data
            
        Returns:
            Tuple of (candles_fetched, candles_inserted)
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Calculate approximate number of candles needed
            timeframe_hours = self._timeframe_to_hours(timeframe)
            limit = min(int(lookback_hours / timeframe_hours) + 10, 1000)
            
            # Fetch fresh data
            candles_data = await self.fetch_candles(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                end_time=end_time
            )
            
            # Filter by time range
            filtered_candles = [
                candle for candle in candles_data
                if start_time <= candle["open_time"] <= end_time
            ]
            
            # Insert into database
            inserted_count = await self.upsert_candles(
                db=db,
                candles_data=filtered_candles,
                symbol=symbol,
                timeframe=timeframe
            )
            
            logger.info(
                f"Market data refreshed for {symbol} {timeframe}",
                symbol=symbol,
                timeframe=timeframe,
                fetched=len(candles_data),
                inserted=inserted_count,
                lookback_hours=lookback_hours
            )
            
            return len(candles_data), inserted_count
            
        except Exception as e:
            logger.error(
                f"Failed to refresh market data for {symbol} {timeframe}",
                symbol=symbol,
                timeframe=timeframe,
                error=str(e)
            )
            raise
    
    def _timeframe_to_hours(self, timeframe: str) -> float:
        """Convert timeframe to hours"""
        timeframe_hours_map = {
            "1m": 1/60, "5m": 5/60, "15m": 15/60, "30m": 30/60,
            "1h": 1, "2h": 2, "4h": 4, "6h": 6, "8h": 8, "12h": 12,
            "1d": 24, "3d": 72, "1w": 168, "1M": 720
        }
        
        return timeframe_hours_map.get(timeframe, 1.0)


# Global market data service instance
market_data_service = MarketDataService()