"""
APScheduler-based job scheduler for trading bots
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from core.config import settings
from core.logging import logger, log_bot_start, log_bot_end, log_error
from core.errors import SchedulerError, BotStateError, BotNotFoundError
from models.bot import Bot, BotState


class SchedulerService:
    """APScheduler-based service for managing bot jobs"""
    
    def __init__(self):
        self.scheduler = self._create_scheduler()
        self.job_store = {}
    
    def _create_scheduler(self) -> AsyncIOScheduler:
        """Create and configure APScheduler instance"""
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_BOTS),
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,  # Prevent concurrent execution of same bot
            'misfire_grace_time': 30  # Allow 30 seconds grace time for missed jobs
        }
        
        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        return scheduler
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def shutdown(self, wait: bool = True):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler stopped")
    
    def get_scheduler(self) -> AsyncIOScheduler:
        """Get scheduler instance"""
        if not self.scheduler.running:
            raise SchedulerError("Scheduler is not running")
        return self.scheduler
    
    def start_bot_job(
        self,
        db: Session,
        bot_id: str
    ) -> str:
        """
        Start a bot job
        
        Args:
            db: Database session
            bot_id: Bot ID
            
        Returns:
            Job ID
        """
        # Load bot
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise BotNotFoundError(f"Bot {bot_id} not found")
        
        # Check if bot can start
        if not bot.can_start:
            raise BotStateError(
                f"Bot {bot_id} cannot be started from state {bot.state.value}",
                {"current_state": bot.state.value, "can_start": bot.can_start}
            )
        
        # Generate unique job ID
        job_id = f"bot_{bot_id}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Start scheduler if not running
            if not self.scheduler.running:
                self.start()
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self.run_bot_cycle,
                trigger=IntervalTrigger(seconds=bot.interval_seconds),
                args=[bot_id],
                id=job_id,
                name=f"Bot {bot_id}",
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=30
            )
            
            # Update bot state
            bot.scheduler_job_id = job_id
            bot.update_state(BotState.RUNNING)
            bot.last_run_at = None  # Will be set on first run
            
            db.commit()
            
            logger.info(
                f"Started bot job {job_id}",
                bot_id=bot_id,
                job_id=job_id,
                interval_seconds=bot.interval_seconds
            )
            
            return job_id
            
        except Exception as e:
            # Rollback state changes
            db.rollback()
            logger.error(
                f"Failed to start bot job",
                bot_id=bot_id,
                error=str(e)
            )
            raise SchedulerError(f"Failed to start bot job: {str(e)}")
    
    def stop_bot_job(
        self,
        db: Session,
        bot_id: str
    ) -> None:
        """
        Stop a bot job
        
        Args:
            db: Database session
            bot_id: Bot ID
        """
        # Load bot
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise BotNotFoundError(f"Bot {bot_id} not found")
        
        # Check if bot can stop
        if not bot.can_stop:
            raise BotStateError(
                f"Bot {bot_id} cannot be stopped from state {bot.state.value}",
                {"current_state": bot.state.value, "can_stop": bot.can_stop}
            )
        
        job_id = bot.scheduler_job_id
        
        try:
            # Remove job from scheduler
            if job_id and self.scheduler.running:
                try:
                    self.scheduler.remove_job(job_id)
                    logger.info(
                        f"Removed bot job {job_id}",
                        bot_id=bot_id,
                        job_id=job_id
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to remove job {job_id} from scheduler",
                        bot_id=bot_id,
                        job_id=job_id,
                        error=str(e)
                    )
            
            # Update bot state
            bot.scheduler_job_id = None
            bot.update_state(BotState.STOPPED)
            
            db.commit()
            
            logger.info(
                f"Stopped bot job",
                bot_id=bot_id,
                job_id=job_id
            )
            
        except Exception as e:
            # Rollback state changes
            db.rollback()
            logger.error(
                f"Failed to stop bot job",
                bot_id=bot_id,
                job_id=job_id,
                error=str(e)
            )
            raise SchedulerError(f"Failed to stop bot job: {str(e)}")
    
    def get_bot_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all running bot jobs"""
        jobs = {}
        
        if self.scheduler.running:
            for job in self.scheduler.get_jobs():
                if job.id.startswith("bot_"):
                    jobs[job.id] = {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger),
                        "func": str(job.func),
                        "args": job.args
                    }
        
        return jobs
    
    def pause_bot_job(self, db: Session, bot_id: str) -> None:
        """Pause a bot job"""
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot or not bot.scheduler_job_id:
            raise BotNotFoundError(f"Bot {bot_id} not found or no active job")
        
        if self.scheduler.running:
            self.scheduler.pause_job(bot.scheduler_job_id)
            bot.update_state(BotState.PAUSED)
            db.commit()
    
    def resume_bot_job(self, db: Session, bot_id: str) -> None:
        """Resume a bot job"""
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot or not bot.scheduler_job_id:
            raise BotNotFoundError(f"Bot {bot_id} not found or no active job")
        
        if self.scheduler.running:
            self.scheduler.resume_job(bot.scheduler_job_id)
            bot.update_state(BotState.RUNNING)
            db.commit()
    
    def run_bot_cycle(self, bot_id: str) -> None:
        """
        CENTRAL BOT EXECUTION LOGIC
        
        This is the main function that executes each bot cycle:
        1. Run ID generation
        2. Bot state verification
        3. Market data refresh
        4. Indicator computation
        5. Strategy evaluation
        6. Signal recording
        7. Order execution
        8. Error handling and rollback
        
        Args:
            bot_id: Bot ID to execute
        """
        import asyncio
        run_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Import here to avoid circular imports
        from core.db import SessionLocal
        from services.market_data import market_data_service
        from services.indicators import indicators_service
        from services.strategies.base import get_strategy
        from services.audit import record_signal, make_inputs_hash, record_run_log
        
        db = SessionLocal()
        
        try:
            # Log bot start
            log_bot_start(bot_id, run_id)
            record_run_log(logger, bot_id, run_id, "start", {})
            
            # Load and verify bot state
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                raise BotNotFoundError(f"Bot {bot_id} not found")
            
            if bot.state != BotState.RUNNING:
                logger.warning(
                    f"Bot {bot_id} is not running, skipping cycle",
                    bot_id=bot_id,
                    current_state=bot.state.value
                )
                return
            
            # Step 1: Update market data
            record_run_log(logger, bot_id, run_id, "market_data_refresh", {})
            
            try:
                # Run async market data operations
                loop = asyncio.get_event_loop()
                
                # Fetch fresh candles
                candles_data = loop.run_until_complete(market_data_service.fetch_candles(
                    symbol=bot.symbol,
                    timeframe=bot.timeframe,
                    limit=100
                ))
                
                # Upsert candles to database
                loop.run_until_complete(market_data_service.upsert_candles(
                    db=db,
                    candles_data=candles_data,
                    symbol=bot.symbol,
                    timeframe=bot.timeframe
                ))
                
                # Get candles from database (synchronous)
                candles = market_data_service.get_candles(
                    db=db,
                    symbol=bot.symbol,
                    timeframe=bot.timeframe,
                    limit=50  # Use recent candles for analysis
                )
                
                if len(candles) < 10:
                    raise ValueError(f"Insufficient data: only {len(candles)} candles")
                
                logger.debug(
                    f"Market data updated for bot {bot_id}",
                    bot_id=bot_id,
                    candles_count=len(candles)
                )
                
            except Exception as e:
                log_error(bot_id, run_id, "market_data_refresh", e)
                raise
            
            # Step 2: Compute indicators
            record_run_log(logger, bot_id, run_id, "indicator_computation", {})
            
            try:
                # Run async indicator computation
                loop = asyncio.get_event_loop()
                indicators = loop.run_until_complete(indicators_service.compute_and_store_indicators(
                    db=db,
                    bot_id=bot_id,
                    candles=candles,
                    timestamp=datetime.utcnow()
                ))
                
                logger.debug(
                    f"Indicators computed for bot {bot_id}",
                    bot_id=bot_id,
                    indicators=list(indicators.keys())
                )
                
            except Exception as e:
                log_error(bot_id, run_id, "indicator_computation", e)
                raise
            
            # Step 3: Strategy evaluation
            record_run_log(logger, bot_id, run_id, "strategy_evaluation", {})
            
            try:
                # Get strategy instance
                strategy = get_strategy(bot.strategy_id.value)
                
                # Evaluate strategy
                strategy_result = strategy.evaluate(
                    candles=candles,
                    indicators=indicators,
                    params=bot.get_params()
                )
                
                logger.debug(
                    f"Strategy evaluated for bot {bot_id}",
                    bot_id=bot_id,
                    signal_type=strategy_result["signal_type"],
                    confidence=strategy_result["confidence"]
                )
                
            except Exception as e:
                log_error(bot_id, run_id, "strategy_evaluation", e)
                raise
            
            # Step 4: Record signal
            record_run_log(logger, bot_id, run_id, "signal_recording", {})
            
            try:
                # Create inputs hash for audit
                inputs_hash = make_inputs_hash({
                    "candles": len(candles),
                    "indicators": list(indicators.keys()),
                    "strategy_params": bot.get_params(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Record signal
                signal = record_signal(
                    db=db,
                    bot=bot,
                    timestamp=datetime.utcnow(),
                    result=strategy_result,
                    inputs_hash=inputs_hash
                )
                
                logger.debug(
                    f"Signal recorded for bot {bot_id}",
                    bot_id=bot_id,
                    signal_id=signal.id,
                    signal_type=strategy_result["signal_type"]
                )
                
            except Exception as e:
                log_error(bot_id, run_id, "signal_recording", e)
                raise
            
            # Step 5: Execute signal (paper trading)
            record_run_log(logger, bot_id, run_id, "signal_execution", {})
            
            try:
                # Get current price (use latest candle close)
                current_price = float(candles[-1].close)
                
                # Execute signal
                from services.execution import execution_service
                
                execution_result = execution_service.execute_signal(
                    db=db,
                    bot=bot,
                    signal_result=strategy_result,
                    current_price=current_price
                )
                
                logger.debug(
                    f"Signal executed for bot {bot_id}",
                    bot_id=bot_id,
                    action=execution_result["action"],
                    order_id=execution_result.get("order_id")
                )
                
            except Exception as e:
                log_error(bot_id, run_id, "signal_execution", e)
                # Don't raise here, let the bot continue running
            
            # Update bot last run time
            bot.last_run_at = datetime.utcnow()
            db.commit()
            
            # Log successful completion
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_bot_end(bot_id, run_id, duration, success=True)
            record_run_log(logger, bot_id, run_id, "completed", {
                "duration_seconds": duration,
                "signal_type": strategy_result["signal_type"],
                "confidence": strategy_result["confidence"],
                "execution_action": execution_result["action"]
            })
            
        except Exception as e:
            # Handle errors and update bot state
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            try:
                # Update bot state to error
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if bot and bot.state == BotState.RUNNING:
                    bot.update_state(BotState.ERROR)
                    db.commit()
            except:
                pass  # Don't let error state update fail
            
            # Log error
            log_bot_end(bot_id, run_id, duration, success=False)
            log_error(bot_id, run_id, "execution", e)
            
            # Re-raise to let APScheduler handle
            raise
        
        finally:
            # Ensure database session is closed
            db.close()


# Global scheduler service instance
scheduler_service = SchedulerService()