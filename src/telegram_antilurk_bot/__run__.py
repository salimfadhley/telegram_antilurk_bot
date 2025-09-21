"""Run module entry point for the Telegram Anti-Lurk Bot.

This module enables running the package directly with:
  python -m telegram_antilurk_bot
  uv run telegram_antilurk_bot

It imports and executes the main function from the main module.
"""

import asyncio
import sys
from pathlib import Path

import structlog

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram_antilurk_bot.main import main

logger = structlog.get_logger(__name__)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error("Application failed to start", error=str(e))
        sys.exit(1)
