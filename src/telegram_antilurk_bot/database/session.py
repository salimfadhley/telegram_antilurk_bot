"""Database session management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    """Get database URL from environment."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return db_url


def get_engine() -> Engine:
    """Get synchronous database engine."""
    db_url = get_database_url()
    return create_engine(db_url)


def get_async_engine() -> AsyncEngine:
    """Get async database engine."""
    db_url = get_database_url()
    # Convert postgresql:// to postgresql+asyncpg:// for async usage
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    return create_async_engine(db_url)


def get_session_maker() -> sessionmaker[Session]:
    """Get synchronous session maker."""
    engine = get_engine()
    return sessionmaker(bind=engine)


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get async session maker."""
    engine = get_async_engine()
    return async_sessionmaker(bind=engine)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
