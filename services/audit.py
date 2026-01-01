"""
Audit service for signal recording and input hashing
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.logging import logger
from models.bot import Bot
from models.signal import Signal, SignalType


def make_inputs_hash(payload: Dict[str, Any]) -> str:
    """
    Create hash for audit trail of inputs
    
    Args:
        payload: Dictionary to hash
        
    Returns:
        SHA-256 hash as hex string
    """
    # Convert to JSON and encode
    json_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def record_signal(
    db: Session,
    bot: Bot,
    timestamp: datetime,
    result: Dict[str, Any],
    inputs_hash: str
) -> Signal:
    """
    Record trading signal in database
    
    Args:
        db: Database session
        bot: Bot instance
        timestamp: Signal timestamp
        result: Strategy evaluation result
        inputs_hash: Hash of inputs for audit
        
    Returns:
        Created Signal instance
    """
    try:
        signal = Signal.create(
            bot_id=bot.id,
            timestamp=timestamp,
            signal_type=SignalType(result["signal_type"]),
            confidence=result["confidence"],
            reason=result["reason"],
            inputs_hash=inputs_hash,
            meta=result.get("metadata", {})
        )
        
        db.add(signal)
        db.commit()
        db.refresh(signal)
        
        logger.info(
            f"Signal recorded: {result['signal_type']} with confidence {result['confidence']:.3f}",
            bot_id=bot.id,
            signal_id=signal.id,
            signal_type=result["signal_type"],
            confidence=result["confidence"],
            reason=result["reason"]
        )
        
        return signal
        
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to record signal",
            bot_id=bot.id,
            signal_type=result.get("signal_type"),
            error=str(e)
        )
        raise


def record_run_log(
    logger_instance,
    bot_id: str,
    run_id: str,
    stage: str,
    extra: Dict[str, Any]
) -> None:
    """
    Record structured log for bot run
    
    Args:
        logger_instance: Logger instance
        bot_id: Bot identifier
        run_id: Run identifier
        stage: Execution stage
        extra: Additional data
    """
    logger_instance.bot_log(
        bot_id=bot_id,
        run_id=run_id,
        stage=stage,
        level="info",
        message=f"Bot cycle stage: {stage}",
        **extra
    )


def get_signal_history(
    db: Session,
    bot_id: str,
    limit: int = 50,
    signal_type: Optional[SignalType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[Signal]:
    """
    Get signal history with filters
    
    Args:
        db: Database session
        bot_id: Bot ID
        limit: Maximum number of signals
        signal_type: Filter by signal type
        start_date: Filter by start date
        end_date: Filter by end date
        
    Returns:
        List of Signal instances
    """
    query = db.query(Signal).filter(Signal.bot_id == bot_id)
    
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type.value)
    
    if start_date:
        query = query.filter(Signal.timestamp >= start_date)
    
    if end_date:
        query = query.filter(Signal.timestamp <= end_date)
    
    signals = query.order_by(desc(Signal.timestamp)).limit(limit).all()
    
    return signals


def get_signal_statistics(
    db: Session,
    bot_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    Calculate signal statistics
    
    Args:
        db: Database session
        bot_id: Bot ID
        days: Number of days to analyze
        
    Returns:
        Dictionary with statistics
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = start_date.replace(day=start_date.day - days)
    
    # Get signals in date range
    signals = db.query(Signal).filter(
        Signal.bot_id == bot_id,
        Signal.timestamp >= start_date,
        Signal.timestamp <= end_date
    ).all()
    
    if not signals:
        return {
            "total_signals": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "hold_signals": 0,
            "avg_confidence": 0.0,
            "high_confidence_signals": 0,
            "last_signal_at": None
        }
    
    # Calculate statistics
    total_signals = len(signals)
    buy_signals = len([s for s in signals if s.is_buy_signal])
    sell_signals = len([s for s in signals if s.is_sell_signal])
    hold_signals = len([s for s in signals if s.is_hold_signal])
    
    confidences = [float(s.confidence) for s in signals]
    avg_confidence = sum(confidences) / len(confidences)
    
    high_confidence_signals = len([s for s in signals if float(s.confidence) >= 0.8])
    
    last_signal = max(signals, key=lambda s: s.timestamp)
    
    return {
        "total_signals": total_signals,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "hold_signals": hold_signals,
        "avg_confidence": round(avg_confidence, 3),
        "high_confidence_signals": high_confidence_signals,
        "last_signal_at": last_signal.timestamp.isoformat()
    }


def verify_signal_integrity(
    db: Session,
    signal_id: str,
    expected_hash: str
) -> bool:
    """
    Verify signal integrity by comparing hashes
    
    Args:
        db: Database session
        signal_id: Signal ID
        expected_hash: Expected input hash
        
    Returns:
        True if hashes match
    """
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    
    if not signal:
        return False
    
    return signal.inputs_hash == expected_hash


def cleanup_old_signals(
    db: Session,
    bot_id: str,
    days_to_keep: int = 90
) -> int:
    """
    Clean up old signals to prevent database bloat
    
    Args:
        db: Database session
        bot_id: Bot ID
        days_to_keep: Number of days of signals to keep
        
    Returns:
        Number of signals deleted
    """
    cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
    
    old_signals = db.query(Signal).filter(
        Signal.bot_id == bot_id,
        Signal.timestamp < cutoff_date
    ).all()
    
    deleted_count = len(old_signals)
    
    for signal in old_signals:
        db.delete(signal)
    
    db.commit()
    
    logger.info(
        f"Cleaned up {deleted_count} old signals for bot {bot_id}",
        bot_id=bot_id,
        deleted_count=deleted_count,
        cutoff_date=cutoff_date.isoformat()
    )
    
    return deleted_count