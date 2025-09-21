"""Telegram Anti-Lurk Bot - A moderation helper for large Telegram communities."""

import asyncio
import sys

import structlog

__version__ = "0.1.0"

# Import async main function
from .main import main as async_main

logger = structlog.get_logger(__name__)


def main() -> None:
    """Synchronous entry point that runs the async main function."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error("Application failed to start", error=str(e))
        sys.exit(1)


__all__ = ["main"]
