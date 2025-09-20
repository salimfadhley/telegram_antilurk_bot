"""Base database configuration - TDD implementation."""

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

Base = declarative_base()


def get_db_url() -> str:
    """Get database URL from environment variable."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Handle both postgres:// and postgresql:// formats
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    return db_url


def get_engine() -> Engine:
    """Create and return database engine."""
    db_url = get_db_url()
    return create_engine(db_url, echo=False, pool_size=10, max_overflow=20)


def get_session() -> Session:
    """Create and return database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
