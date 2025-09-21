"""Main entry point for the Telegram Anti-Lurk Bot."""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram_antilurk_bot.main import main  # type: ignore[import-not-found]

if __name__ == "__main__":
    asyncio.run(main())
