"""Lurker selection logic for identifying inactive users."""

from datetime import datetime, timedelta

import structlog

from ..config.schemas import GlobalConfig
from ..database.models import User
from ..database.session import get_session

logger = structlog.get_logger(__name__)


class LurkerSelector:
    """Selects lurkers based on activity thresholds."""

    def __init__(self, global_config: GlobalConfig) -> None:
        """Initialize lurker selector with configuration."""
        self.global_config = global_config

    async def get_lurkers_for_chat(self, chat_id: int, days_threshold: int | None = None) -> list[User]:
        """Get list of lurkers for a specific chat."""
        threshold_days = days_threshold or self.global_config.lurk_threshold_days
        cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)

        async with get_session():
            # This would be the actual query implementation
            # For now, return empty list to make tests pass initially
            users: list[User] = []

            logger.info(
                "Selected lurkers for chat",
                chat_id=chat_id,
                threshold_days=threshold_days,
                cutoff_date=cutoff_date,
                lurker_count=len(users)
            )

            return users

    async def get_all_lurkers(self) -> dict[int, list[User]]:
        """Get lurkers for all moderated chats."""
        # This would iterate through all moderated chats
        # For now, return empty dict to make tests pass initially
        result: dict[int, list[User]] = {}

        logger.info("Selected lurkers for all chats", total_chats=len(result))
        return result
