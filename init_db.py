#!/usr/bin/env python3
"""
Database initialization and migration script
"""
import asyncio
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from core.db import Base, engine
from models import *
from core.security import get_password_hash


def init_database():
    """Initialize database with tables and default data"""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a default admin user
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@tradingbot.com").first()
        
        if not admin_user:
            print("Creating default admin user...")
            admin_user = User(
                id="admin_default_001",
                email="admin@tradingbot.com",
                password_hash=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created: admin@tradingbot.com / admin123")
        else:
            print("✅ Admin user already exists")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("✅ Database initialization completed")


def drop_database():
    """Drop all database tables (⚠️  This will delete all data)"""
    print("⚠️  Dropping all database tables...")
    response = input("Are you sure you want to delete ALL data? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
    else:
        print("❌ Operation cancelled")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            init_database()
        elif command == "drop":
            drop_database()
        else:
            print("Usage: python init_db.py [init|drop]")
            print("  init - Create tables and default data")
            print("  drop - Drop all tables (⚠️  deletes all data)")
    else:
        init_database()