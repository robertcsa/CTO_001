"""
Database setup and configuration
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator
from core.config import settings


# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

# Base model for all ORM models
Base = declarative_base()

# MetaData for Alembic migrations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> redis.Redis:
    """Dependency to get Redis client"""
    return redis_client


def test_connection():
    """Test database and Redis connections"""
    try:
        # Test database
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection successful")
        
        # Test Redis
        redis_client.ping()
        print("✅ Redis connection successful")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        raise