"""
Bot management API routes
"""
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_db
from api.deps import get_current_active_user, get_bot_or_404
from schemas.bot import (
    BotCreate, BotUpdate, BotResponse, BotStatusResponse,
    BotStartRequest, BotStopRequest, BotStartResponse, BotStopResponse
)
from models.bot import Bot, BotState
from models.user import User
from services.scheduler import scheduler_service


router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new trading bot
    """
    try:
        # Validate strategy parameters
        from services.strategies.base import validate_strategy_params
        if not validate_strategy_params(bot_data.strategy_id.value, bot_data.params or {}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid strategy parameters"
            )
        
        # Create bot instance
        db_bot = Bot(
            user_id=current_user.id,
            name=bot_data.name,
            asset_type=bot_data.asset_type,
            symbol=bot_data.symbol.upper(),
            timeframe=bot_data.timeframe,
            strategy_id=bot_data.strategy_id,
            interval_seconds=bot_data.interval_seconds,
            params=bot_data.params or {}
        )
        
        db.add(db_bot)
        db.commit()
        db.refresh(db_bot)
        
        return db_bot
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bot: {str(e)}"
        )


@router.get("/", response_model=List[BotResponse])
async def list_bots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get list of user's bots
    """
    bots = db.query(Bot).filter(
        Bot.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot: Bot = Depends(get_bot_or_404)
):
    """
    Get bot by ID
    """
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_data: BotUpdate,
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update bot configuration
    """
    try:
        # Check if bot is running
        if bot.state == BotState.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update bot while it's running"
            )
        
        # Update fields
        update_data = bot_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "params" and value is not None:
                # Validate strategy parameters if changed
                from services.strategies.base import validate_strategy_params
                if not validate_strategy_params(bot.strategy_id.value, value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid strategy parameters"
                    )
            setattr(bot, field, value)
        
        bot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(bot)
        
        return bot
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bot: {str(e)}"
        )


@router.delete("/{bot_id}")
async def delete_bot(
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete bot
    """
    try:
        # Stop bot if running
        if bot.state == BotState.RUNNING:
            scheduler_service.stop_bot_job(db, bot.id)
        
        # Delete bot (cascade will delete related records)
        db.delete(bot)
        db.commit()
        
        return {"message": "Bot deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bot: {str(e)}"
        )


@router.post("/{bot_id}/start", response_model=BotStartResponse)
async def start_bot(
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Start trading bot
    """
    try:
        if not bot.can_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bot cannot be started from state {bot.state.value}"
            )
        
        # Start bot job
        job_id = scheduler_service.start_bot_job(db, bot.id)
        
        return BotStartResponse(
            status="started",
            job_id=job_id,
            message=f"Bot '{bot.name}' started successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}"
        )


@router.post("/{bot_id}/stop", response_model=BotStopResponse)
async def stop_bot(
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Stop trading bot
    """
    try:
        if not bot.can_stop:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bot cannot be stopped from state {bot.state.value}"
            )
        
        # Stop bot job
        scheduler_service.stop_bot_job(db, bot.id)
        
        return BotStopResponse(
            status="stopped",
            message=f"Bot '{bot.name}' stopped successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop bot: {str(e)}"
        )


@router.post("/{bot_id}/pause")
async def pause_bot(
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pause trading bot
    """
    try:
        if bot.state != BotState.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only running bots can be paused"
            )
        
        scheduler_service.pause_bot_job(db, bot.id)
        
        return {"message": f"Bot '{bot.name}' paused successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause bot: {str(e)}"
        )


@router.post("/{bot_id}/resume")
async def resume_bot(
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Resume paused trading bot
    """
    try:
        if bot.state != BotState.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only paused bots can be resumed"
            )
        
        scheduler_service.resume_bot_job(db, bot.id)
        
        return {"message": f"Bot '{bot.name}' resumed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume bot: {str(e)}"
        )


@router.get("/{bot_id}/status", response_model=BotStatusResponse)
async def get_bot_status(
    bot: Bot = Depends(get_bot_or_404)
):
    """
    Get bot status information
    """
    return BotStatusResponse(
        id=bot.id,
        name=bot.name,
        state=bot.state,
        last_run_at=bot.last_run_at,
        is_running=bot.is_running,
        can_start=bot.can_start,
        can_stop=bot.can_stop
    )


@router.get("/{bot_id}/jobs")
async def get_bot_jobs(
    bot: Bot = Depends(get_bot_or_404),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get scheduler job information for bot
    """
    try:
        jobs = scheduler_service.get_bot_jobs()
        bot_jobs = {job_id: job_info for job_id, job_info in jobs.items() 
                   if bot_id in job_id}
        
        return {
            "bot_id": bot.id,
            "scheduler_job_id": bot.scheduler_job_id,
            "jobs": bot_jobs
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job information: {str(e)}"
        )


@router.post("/{bot_id}/test-cycle")
async def test_bot_cycle(
    bot: Bot = Depends(get_bot_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test bot cycle manually (for debugging)
    """
    try:
        if bot.state == BotState.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot test running bot"
            )
        
        # Run bot cycle manually
        scheduler_service.run_bot_cycle(bot.id)
        
        return {"message": f"Bot '{bot.name}' test cycle completed"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test bot cycle: {str(e)}"
        )


@router.get("/{bot_id}/config")
async def get_bot_config(
    bot: Bot = Depends(get_bot_or_404),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed bot configuration and strategy info
    """
    try:
        from services.strategies.base import get_strategy
        
        strategy = get_strategy(bot.strategy_id.value)
        strategy_info = strategy.get_strategy_info() if hasattr(strategy, 'get_strategy_info') else {}
        
        return {
            "bot": {
                "id": bot.id,
                "name": bot.name,
                "asset_type": bot.asset_type.value,
                "symbol": bot.symbol,
                "timeframe": bot.timeframe,
                "strategy_id": bot.strategy_id.value,
                "interval_seconds": bot.interval_seconds,
                "params": bot.get_params(),
                "state": bot.state.value,
                "created_at": bot.created_at.isoformat(),
                "last_run_at": bot.last_run_at.isoformat() if bot.last_run_at else None
            },
            "strategy": strategy_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot config: {str(e)}"
        )