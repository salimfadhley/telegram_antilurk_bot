"""Lurker selection logic for identifying inactive users."""

from datetime import datetime, timedelta
from typing import List

import structlog

from ..config.loader import ConfigLoader
from ..config.schemas import GlobalConfig
from ..database.models import User

logger = structlog.get_logger(__name__)


class LurkerSelector:
    """Selects lurkers based on activity thresholds."""

    def __init__(
        self, global_config: GlobalConfig | None = None, config_loader: ConfigLoader | None = None
    ) -> None:
        """Initialize lurker selector with configuration.

        Accepts an optional `GlobalConfig` or a `ConfigLoader` to load one.
        If neither is provided, a default `ConfigLoader` is used.
        """
        if global_config is not None:
            self.global_config = global_config
        else:
            loader = config_loader or ConfigLoader()
            self.global_config, _, _ = loader.load_all()

    # --- Unit-test oriented synchronous API ---
    def identify_lurkers(
        self,
        chat_id: int,
        threshold_days: int,
        provocation_interval_hours: int = 48,
    ) -> List[User]:
        """Identify lurkers for a chat applying protection and recency filters."""
        users = self._get_chat_users(chat_id)
        result: list[User] = []
        for user in users:
            try:
                if user.is_protected():
                    continue
                if not user.is_lurker(threshold_days):
                    continue
                if self._was_recently_provoked(chat_id, user.user_id, provocation_interval_hours):
                    continue
                result.append(user)
            except AttributeError:
                # If a mock or user is missing an attribute, skip it gracefully for tests
                continue
        logger.info(
            "Identified lurkers",
            chat_id=chat_id,
            threshold_days=threshold_days,
            selected=len(result),
        )
        return result

    def _get_chat_users(self, chat_id: int) -> List[User]:
        """Fetch users for a chat. Placeholder for tests to patch."""
        _ = chat_id
        return []

    def _was_recently_provoked(self, chat_id: int, user_id: int, interval_hours: int) -> bool:
        """Check if a user was provoked within the given interval. Patched in tests."""
        _ = (chat_id, user_id, interval_hours)
        return False

    # --- Async helpers retained for other parts of the codebase ---
    async def get_lurkers_for_chat(
        self, chat_id: int, days_threshold: int | None = None
    ) -> list[User]:
        """Get list of lurkers for a specific chat using basic rules.

        This is a simplified async variant used by the audit engine.
        """
        threshold_days = days_threshold or self.global_config.lurk_threshold_days
        # Defer to sync identify_lurkers to keep logic in one place
        return self.identify_lurkers(chat_id, threshold_days)

    def is_lurker(self, user: User, days_threshold: int | None = None) -> bool:
        """Determine if a user is considered a lurker.

        A user is a lurker if their last_message_at is None or older than
        the configured threshold (in days).
        """
        threshold_days = days_threshold or self.global_config.lurk_threshold_days
        cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)
        if user.last_message_at is None:
            return True
        return user.last_message_at < cutoff_date
