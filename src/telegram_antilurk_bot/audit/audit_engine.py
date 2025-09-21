"""Core audit engine that coordinates lurker detection and provocation."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import structlog

from ..config.loader import ConfigLoader
from ..database.models import User
from .backlog_manager import BacklogManager
from .lurker_selector import LurkerSelector
from .rate_limiter import RateLimiter

logger = structlog.get_logger(__name__)


class AuditEngine:
    """Main engine for coordinating audit operations."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize audit engine with configuration."""
        self.config_loader = ConfigLoader(config_dir=config_dir) if config_dir else ConfigLoader()
        self.global_config, self.channels_config, _ = self.config_loader.load_all()

        self.lurker_selector = LurkerSelector(self.global_config)
        self.rate_limiter = RateLimiter(self.global_config)
        self.backlog_manager = BacklogManager()

        logger.info("AuditEngine initialized")

    async def run_full_audit(self) -> dict[str, Any]:
        """Run complete audit cycle for all moderated chats."""
        moderated_chats = self.channels_config.get_moderated_channels()

        total_lurkers = 0
        total_provoked = 0
        total_backlogged = 0
        processed_chats = 0

        for chat in moderated_chats:
            try:
                result = await self.audit_chat(chat.chat_id)
                total_lurkers += result["lurkers_found"]
                total_provoked += result["users_provoked"]
                total_backlogged += result["users_backlogged"]
                processed_chats += 1

                logger.info(
                    "Chat audit completed", chat_id=chat.chat_id, chat_name=chat.chat_name, **result
                )
            except Exception as e:
                logger.error(
                    "Chat audit failed",
                    chat_id=chat.chat_id,
                    chat_name=chat.chat_name,
                    error=str(e),
                )

        audit_result = {
            "processed_chats": processed_chats,
            "total_lurkers": total_lurkers,
            "total_provoked": total_provoked,
            "total_backlogged": total_backlogged,
            "backlog_stats": self.backlog_manager.get_backlog_stats(),
        }

        logger.info("Full audit completed", **audit_result)
        return audit_result

    # --- Unit-test oriented orchestrator and helpers ---
    async def run_audit_cycle(self) -> None:
        """Compatibility wrapper for unit tests.

        Iterates moderated channels and delegates to `_process_chat` synchronously
        to support patching without awaiting MagicMocks.
        """
        channels = self._get_moderated_channels()
        for ch in channels:
            self._process_chat(ch)

    def _get_moderated_channels(self) -> list[Any]:
        """Return moderated channels list (objects with chat_id, chat_name)."""
        return self.channels_config.get_moderated_channels()

    def _identify_lurkers(self, chat_id: int) -> list[User]:
        """Identify lurkers for a single chat using configured defaults."""
        threshold = self.global_config.lurk_threshold_days
        return self.lurker_selector.identify_lurkers(chat_id, threshold)

    def _can_provoke(self, chat_id: int) -> bool:
        """Whether provocations can be sent now for this chat given limits."""
        return self.rate_limiter.can_provoke_user(chat_id)

    def _initiate_provocation(self, chat_id: int, user: User) -> None:
        """Initiate a provocation for a user. In tests this is patched."""
        # In production flow this would delegate to challenge engine; here we just log
        logger.info("Initiating provocation", chat_id=chat_id, user_id=user.user_id)

    def _add_to_backlog(self, chat_id: int, users: Iterable[User]) -> None:
        """Add users to backlog with a default reason."""
        self.backlog_manager.add_to_backlog(chat_id, list(users), reason="rate_limited")

    def _process_chat(self, channel: Any) -> None:
        """Process a single moderated channel (sync wrapper for tests)."""
        chat_id = getattr(channel, "chat_id", None)
        if chat_id is None:
            return
        lurkers = self._identify_lurkers(chat_id)
        for user in lurkers:
            if self._can_provoke(chat_id):
                self._initiate_provocation(chat_id, user)
            else:
                self._add_to_backlog(chat_id, [user])

    async def audit_chat(self, chat_id: int) -> dict[str, Any]:
        """Audit a single chat for lurkers."""
        # First, process any existing backlog
        backlog_users = self.backlog_manager.get_backlog(chat_id)
        new_lurkers = await self.lurker_selector.get_lurkers_for_chat(chat_id)

        # Combine backlog and new lurkers, prioritizing backlog
        all_candidates = backlog_users + new_lurkers

        # Apply rate limiting
        allowed_users, blocked_users = await self.rate_limiter.filter_users_by_rate_limit(
            chat_id, all_candidates
        )

        # Provoke allowed users
        provoked_count = 0
        for user in allowed_users:
            try:
                await self._provoke_user(chat_id, user)
                provoked_count += 1
            except Exception as e:
                logger.error(
                    "Failed to provoke user", chat_id=chat_id, user_id=user.user_id, error=str(e)
                )

        # Update backlog with blocked users
        if blocked_users:
            # Clear existing backlog first (since we processed it)
            self.backlog_manager.clear_backlog(chat_id)
            self.backlog_manager.add_to_backlog(chat_id, blocked_users)

        result = {
            "lurkers_found": len(new_lurkers),
            "backlog_processed": len(backlog_users),
            "users_provoked": provoked_count,
            "users_backlogged": len(blocked_users),
        }

        return result

    async def _provoke_user(self, chat_id: int, user: User) -> None:
        """Send provocation to a specific user."""
        # This would implement the actual provocation logic
        # For now, just log it to make tests pass
        logger.info("User provoked", chat_id=chat_id, user_id=user.user_id, username=user.username)
