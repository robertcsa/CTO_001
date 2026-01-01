"""
Base strategy classes and protocols
"""
from abc import ABC, abstractmethod
from typing import Protocol, TypedDict, List, Dict, Any, Optional
from datetime import datetime
from models.candle import MarketCandle
from models.indicator import IndicatorSnapshot
from models.signal import SignalType


class StrategyResult(TypedDict):
    """Strategy evaluation result"""
    signal_type: SignalType
    confidence: float  # 0.0 to 1.0
    reason: str
    metadata: Dict[str, Any]


class Strategy(Protocol):
    """Strategy protocol for trading strategies"""
    
    @property
    def strategy_id(self) -> str:
        """Unique identifier for the strategy"""
        ...
    
    @property
    def name(self) -> str:
        """Human readable strategy name"""
        ...
    
    @property
    def description(self) -> str:
        """Strategy description"""
        ...
    
    def evaluate(
        self,
        candles: List[MarketCandle],
        indicators: Dict[str, Any],
        params: Dict[str, Any]
    ) -> StrategyResult:
        """
        Evaluate market data and generate trading signal
        
        Args:
            candles: Historical market candles
            indicators: Calculated technical indicators
            params: Strategy parameters
            
        Returns:
            StrategyResult with signal and confidence
        """
        ...
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate strategy parameters
        
        Args:
            params: Strategy parameters to validate
            
        Returns:
            True if parameters are valid
        """
        ...
    
    def get_required_data_points(self, params: Dict[str, Any]) -> int:
        """
        Get minimum required data points for strategy
        
        Args:
            params: Strategy parameters
            
        Returns:
            Minimum number of candles required
        """
        ...


class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    @property
    @abstractmethod
    def strategy_id(self) -> str:
        """Unique identifier for the strategy"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human readable strategy name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Strategy description"""
        pass
    
    @abstractmethod
    def evaluate(
        self,
        candles: List[MarketCandle],
        indicators: Dict[str, Any],
        params: Dict[str, Any]
    ) -> StrategyResult:
        """Evaluate market data and generate trading signal"""
        pass
    
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate strategy parameters"""
        pass
    
    @abstractmethod
    def get_required_data_points(self, params: Dict[str, Any]) -> int:
        """Get minimum required data points"""
        pass


class StrategyRegistry:
    """Registry for available strategies"""
    
    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
    
    def register(self, strategy: Strategy):
        """Register a strategy"""
        self._strategies[strategy.strategy_id] = strategy
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get strategy by ID"""
        return self._strategies.get(strategy_id)
    
    def list_strategies(self) -> List[Dict[str, str]]:
        """List all available strategies"""
        return [
            {
                "strategy_id": strategy.strategy_id,
                "name": strategy.name,
                "description": strategy.description
            }
            for strategy in self._strategies.values()
        ]
    
    def is_valid_strategy(self, strategy_id: str) -> bool:
        """Check if strategy ID is valid"""
        return strategy_id in self._strategies


# Global strategy registry
strategy_registry = StrategyRegistry()


def get_strategy(strategy_id: str) -> Strategy:
    """Get strategy instance by ID"""
    strategy = strategy_registry.get_strategy(strategy_id)
    if strategy is None:
        raise ValueError(f"Unknown strategy: {strategy_id}")
    return strategy


def validate_strategy_params(strategy_id: str, params: Dict[str, Any]) -> bool:
    """Validate strategy parameters"""
    strategy = get_strategy(strategy_id)
    return strategy.validate_params(params)


def get_strategy_requirements(strategy_id: str, params: Dict[str, Any]) -> int:
    """Get strategy data requirements"""
    strategy = get_strategy(strategy_id)
    return strategy.get_required_data_points(params)


def create_hold_signal(
    reason: str = "Hold signal - no trading opportunity",
    confidence: float = 0.5
) -> StrategyResult:
    """Create a hold signal"""
    return StrategyResult(
        signal_type=SignalType.HOLD,
        confidence=confidence,
        reason=reason,
        metadata={}
    )


def create_buy_signal(
    reason: str,
    confidence: float,
    metadata: Dict[str, Any] = None
) -> StrategyResult:
    """Create a buy signal"""
    return StrategyResult(
        signal_type=SignalType.BUY,
        confidence=max(0.0, min(1.0, confidence)),  # Clamp to 0-1
        reason=reason,
        metadata=metadata or {}
    )


def create_sell_signal(
    reason: str,
    confidence: float,
    metadata: Dict[str, Any] = None
) -> StrategyResult:
    """Create a sell signal"""
    return StrategyResult(
        signal_type=SignalType.SELL,
        confidence=max(0.0, min(1.0, confidence)),  # Clamp to 0-1
        reason=reason,
        metadata=metadata or {}
    )