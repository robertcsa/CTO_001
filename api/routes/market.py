"""
Market data API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from core.db import get_db
from api.deps import get_current_active_user, get_bot_or_404
from schemas.market import (
    MarketDataRequest, CandlesResponse, CandleResponse,
    IndicatorsRequest, IndicatorResponse
)
from services.market_data import market_data_service
from services.indicators import indicators_service
from models.bot import Bot
from models.candle import MarketCandle
from models.indicator import IndicatorSnapshot
from models.user import User


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/candles", response_model=CandlesResponse)
async def get_candles(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    limit: int = Query(100, ge=1, le=1000, description="Number of candles"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get market candles for symbol and timeframe
    """
    try:
        candles = market_data_service.get_candles(
            db=db,
            symbol=symbol.upper(),
            timeframe=timeframe,
            start_time=start_date,
            end_time=end_date,
            limit=limit
        )
        
        candle_responses = [CandleResponse.from_orm(candle) for candle in candles]
        
        return CandlesResponse(
            candles=candle_responses,
            total=len(candle_responses),
            symbol=symbol.upper(),
            timeframe=timeframe
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candles: {str(e)}"
        )


@router.post("/refresh")
async def refresh_market_data(
    request: MarketDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Refresh market data for symbol and timeframe
    """
    try:
        import asyncio
        
        loop = asyncio.get_event_loop()
        fetched, inserted = loop.run_until_complete(
            market_data_service.refresh_market_data(
                db=db,
                symbol=request.symbol.upper(),
                timeframe=request.timeframe,
                lookback_hours=24
            )
        )
        
        return {
            "symbol": request.symbol.upper(),
            "timeframe": request.timeframe,
            "candles_fetched": fetched,
            "candles_inserted": inserted,
            "message": f"Successfully refreshed market data"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh market data: {str(e)}"
        )


@router.get("/candles/{symbol}/{timeframe}")
async def get_candles_for_symbol(
    symbol: str,
    timeframe: str,
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get candles for specific symbol and timeframe
    """
    return await get_candles(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        db=db,
        current_user=current_user
    )


@router.get("/indicators", response_model=List[IndicatorResponse])
async def get_indicators(
    bot_id: str = Query(..., description="Bot ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of indicators"),
    indicator_type: Optional[str] = Query(None, description="Filter by indicator type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get technical indicators for bot
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
        
        indicators = indicators_service.get_latest_indicators(
            db=db,
            bot_id=bot_id,
            limit=limit,
            indicator_type=indicator_type
        )
        
        return [IndicatorResponse.from_orm(ind) for ind in indicators]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get indicators: {str(e)}"
        )


@router.post("/indicators/compute")
async def compute_indicators(
    bot_id: str,
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    limit: int = Query(50, ge=10, le=200, description="Number of candles for computation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compute technical indicators for bot (manual trigger)
    """
    try:
        import asyncio
        
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
        
        # Get candles
        candles = market_data_service.get_candles(
            db=db,
            symbol=symbol.upper(),
            timeframe=timeframe,
            limit=limit
        )
        
        if len(candles) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient data: only {len(candles)} candles available"
            )
        
        # Compute indicators
        loop = asyncio.get_event_loop()
        indicators = loop.run_until_complete(
            indicators_service.compute_and_store_indicators(
                db=db,
                bot_id=bot_id,
                candles=candles,
                timestamp=datetime.utcnow()
            )
        )
        
        return {
            "bot_id": bot_id,
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "candles_used": len(candles),
            "indicators_computed": list(indicators.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute indicators: {str(e)}"
        )


@router.get("/symbols")
async def get_supported_symbols(
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of supported trading symbols
    """
    from core.config import MARKET_DATA_SYMBOLS
    
    if asset_type:
        if asset_type not in MARKET_DATA_SYMBOLS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported asset type: {asset_type}"
            )
        return {
            "asset_type": asset_type,
            "symbols": MARKET_DATA_SYMBOLS[asset_type]
        }
    
    return MARKET_DATA_SYMBOLS


@router.get("/timeframes")
async def get_supported_timeframes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of supported timeframes
    """
    from core.config import TIMEFRAMES, SUPPORTED_TIMEFRAMES
    
    return {
        "timeframes": SUPPORTED_TIMEFRAMES,
        "descriptions": TIMEFRAMES
    }


@router.get("/candles/stats/{symbol}/{timeframe}")
async def get_candle_stats(
    symbol: str,
    timeframe: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get statistics for candle data
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        candles = market_data_service.get_candles(
            db=db,
            symbol=symbol.upper(),
            timeframe=timeframe,
            start_time=start_date,
            end_time=end_date
        )
        
        if not candles:
            return {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "period_days": days,
                "total_candles": 0,
                "message": "No data available for specified period"
            }
        
        # Calculate statistics
        closes = [float(c.close) for c in candles]
        volumes = [float(c.volume) for c in candles]
        
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "period_days": days,
            "total_candles": len(candles),
            "date_range": {
                "start": candles[-1].timestamp.isoformat() if candles else None,
                "end": candles[0].timestamp.isoformat() if candles else None
            },
            "price_stats": {
                "min": min(closes),
                "max": max(closes),
                "latest": closes[0] if closes else 0,
                "change_24h": closes[0] - closes[-1] if len(closes) > 1 else 0,
                "change_24h_pct": ((closes[0] - closes[-1]) / closes[-1] * 100) if len(closes) > 1 and closes[-1] != 0 else 0
            },
            "volume_stats": {
                "total": sum(volumes),
                "average": sum(volumes) / len(volumes) if volumes else 0,
                "min": min(volumes) if volumes else 0,
                "max": max(volumes) if volumes else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candle stats: {str(e)}"
        )