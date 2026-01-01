"""
Trading Bot System - Core Configuration

FastAPI + SQLAlchemy + PostgreSQL + Redis + APScheduler
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Trading Bot System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD") 
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY", min_length=32)
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Market Data API
    MARKET_DATA_API_KEY: Optional[str] = Field(default=None, env="MARKET_DATA_API_KEY")
    MARKET_DATA_BASE_URL: str = Field(default="https://api.binance.com", env="MARKET_DATA_BASE_URL")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Scheduler
    MAX_CONCURRENT_BOTS: int = Field(default=50, env="MAX_CONCURRENT_BOTS")
    
    # Paper Trading
    DEFAULT_PAPER_TRADING: bool = Field(default=True, env="DEFAULT_PAPER_TRADING")
    PAPER_TRADING_BALANCE: float = Field(default=10000.0, env="PAPER_TRADING_BALANCE")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


# Global settings instance
settings = Settings()


# Market Data Configuration
MARKET_DATA_SYMBOLS = {
    "crypto": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"],
    "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
    "stocks": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
}

TIMEFRAMES = {
    "1m": "1 minute",
    "5m": "5 minutes", 
    "15m": "15 minutes",
    "30m": "30 minutes",
    "1h": "1 hour",
    "4h": "4 hours",
    "1d": "1 day",
    "1w": "1 week"
}

SUPPORTED_TIMEFRAMES = list(TIMEFRAMES.keys())