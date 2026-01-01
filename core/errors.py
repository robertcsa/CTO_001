"""
Custom exception classes for trading bot system
"""
from typing import Any, Dict, Optional


class TradingBotException(Exception):
    """Base exception class for trading bot system"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class MarketDataError(TradingBotException):
    """Exception raised when market data operations fail"""
    pass


class StrategyError(TradingBotException):
    """Exception raised when strategy evaluation fails"""
    pass


class ExecutionError(TradingBotException):
    """Exception raised when order execution fails"""
    pass


class SchedulerError(TradingBotException):
    """Exception raised when scheduler operations fail"""
    pass


class AuthenticationError(TradingBotException):
    """Exception raised when authentication fails"""
    pass


class AuthorizationError(TradingBotException):
    """Exception raised when authorization fails"""
    pass


class ValidationError(TradingBotException):
    """Exception raised when data validation fails"""
    pass


class DatabaseError(TradingBotException):
    """Exception raised when database operations fail"""
    pass


class ConfigurationError(TradingBotException):
    """Exception raised when configuration is invalid"""
    pass


class BotNotFoundError(TradingBotException):
    """Exception raised when bot is not found"""
    pass


class BotStateError(TradingBotException):
    """Exception raised when bot state is invalid"""
    pass


class SignalGenerationError(TradingBotException):
    """Exception raised when signal generation fails"""
    pass


class InsufficientDataError(TradingBotException):
    """Exception raised when there's insufficient data for analysis"""
    pass


class RateLimitError(TradingBotException):
    """Exception raised when API rate limit is exceeded"""
    pass


class TimeoutError(TradingBotException):
    """Exception raised when operations timeout"""
    pass


class PositionError(TradingBotException):
    """Exception raised when position operations fail"""
    pass