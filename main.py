"""
Main FastAPI application
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from core.config import settings
from core.db import test_connection, engine
from core.logging import logger
from services.scheduler import scheduler_service
from services.strategies.blue_sky import blue_sky_strategy
from services.strategies.base import strategy_registry

# Register strategies
strategy_registry.register(blue_sky_strategy)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    try:
        # Test connections
        test_connection()
        
        # Start scheduler
        scheduler_service.start()
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    try:
        # Stop scheduler
        scheduler_service.shutdown()
        
        # Close database connections
        engine.dispose()
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Application shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Kódalapú Trading Bot rendszer FastAPI backend-del",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.routes import auth, bots, market, trading

app.include_router(auth.router)
app.include_router(bots.router)
app.include_router(market.router)
app.include_router(trading.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} v{settings.APP_VERSION}",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        # Test scheduler
        scheduler_running = scheduler_service.scheduler.running
        
        return {
            "status": "healthy",
            "database": "connected",
            "scheduler": "running" if scheduler_running else "stopped",
            "version": settings.APP_VERSION
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.get("/info")
async def app_info():
    """Application information endpoint"""
    from core.config import MARKET_DATA_SYMBOLS, TIMEFRAMES, SUPPORTED_TIMEFRAMES
    from services.strategies.base import strategy_registry
    
    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG
        },
        "database": {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB
        },
        "redis": {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB
        },
        "scheduler": {
            "max_concurrent_bots": settings.MAX_CONCURRENT_BOTS
        },
        "market_data": {
            "base_url": settings.MARKET_DATA_BASE_URL,
            "rate_limit_per_minute": settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            "symbols": MARKET_DATA_SYMBOLS,
            "timeframes": SUPPORTED_TIMEFRAMES
        },
        "strategies": strategy_registry.list_strategies(),
        "paper_trading": {
            "enabled": settings.DEFAULT_PAPER_TRADING,
            "default_balance": settings.PAPER_TRADING_BALANCE
        }
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "Internal server error occurred",
                "status_code": 500
            }
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )