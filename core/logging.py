"""
Structured logging configuration for trading bot system
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from core.config import settings


class TradingBotLogger:
    """Structured logger for trading bot operations"""
    
    def __init__(self, name: str = "trading_bot"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with JSON formatter"""
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            
            # JSON formatter
            json_formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            console_handler.setFormatter(json_formatter)
            self.logger.addHandler(console_handler)
            
            # Set level
            self.logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
            
            # Prevent duplicate logs
            self.logger.propagate = False
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal logging method"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            **kwargs
        }
        
        if extra:
            log_data.update(extra)
        
        self.logger.log(level, json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def bot_log(self, bot_id: str, run_id: Optional[str] = None, stage: Optional[str] = None, 
                level: str = "info", message: str = "", **extra):
        """Log bot-specific message"""
        log_data = {
            "bot_id": bot_id,
            "run_id": run_id,
            "stage": stage,
            **extra
        }
        
        if level == "info":
            self.info(message, **log_data)
        elif level == "warning":
            self.warning(message, **log_data)
        elif level == "error":
            self.error(message, **log_data)
        elif level == "debug":
            self.debug(message, **log_data)


# Global logger instance
logger = TradingBotLogger()


# Utility functions for bot logging
def log_bot_start(bot_id: str, run_id: str):
    """Log bot start"""
    logger.bot_log(bot_id, run_id, "start", "info", "Bot cycle started")


def log_bot_end(bot_id: str, run_id: str, duration: float, success: bool = True):
    """Log bot end"""
    logger.bot_log(
        bot_id, run_id, "end", "info" if success else "error",
        "Bot cycle completed" if success else "Bot cycle failed",
        duration_seconds=duration,
        success=success
    )


def log_signal_generated(bot_id: str, signal_type: str, confidence: float, reason: str):
    """Log signal generation"""
    logger.bot_log(
        bot_id, stage="signal_generation", level="info",
        message=f"Signal generated: {signal_type}",
        signal_type=signal_type,
        confidence=confidence,
        reason=reason
    )


def log_order_execution(bot_id: str, action: str, order_id: str, price: float, quantity: float):
    """Log order execution"""
    logger.bot_log(
        bot_id, stage="order_execution", level="info",
        message=f"Order executed: {action}",
        action=action,
        order_id=order_id,
        price=price,
        quantity=quantity
    )


def log_error(bot_id: str, run_id: str, stage: str, error: Exception, **extra):
    """Log error with context"""
    logger.bot_log(
        bot_id, run_id, stage, "error",
        f"Error in {stage}: {str(error)}",
        error_type=type(error).__name__,
        error_message=str(error),
        **extra
    )