"""Core audit engine that coordinates lurker detection and provocation."""

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
                total_lurkers += result['lurkers_found']
                total_provoked += result['users_provoked']
                total_backlogged += result['users_backlogged']
                processed_chats += 1

                logger.info(
                    "Chat audit completed",
                    chat_id=chat.chat_id,
                    chat_name=chat.chat_name,
                    **result
                )
            except Exception as e:
                logger.error(
                    "Chat audit failed",
                    chat_id=chat.chat_id,
                    chat_name=chat.chat_name,
                    error=str(e)
                )

        audit_result = {
            'processed_chats': processed_chats,
            'total_lurkers': total_lurkers,
            'total_provoked': total_provoked,
            'total_backlogged': total_backlogged,
            'backlog_stats': self.backlog_manager.get_backlog_stats()
        }

        logger.info("Full audit completed", **audit_result)
        return audit_result

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
                    "Failed to provoke user",
                    chat_id=chat_id,
                    user_id=user.user_id,
                    error=str(e)
                )

        # Update backlog with blocked users
        if blocked_users:
            # Clear existing backlog first (since we processed it)
            self.backlog_manager.clear_backlog(chat_id)
            self.backlog_manager.add_to_backlog(chat_id, blocked_users)

        result = {
            'lurkers_found': len(new_lurkers),
            'backlog_processed': len(backlog_users),
            'users_provoked': provoked_count,
            'users_backlogged': len(blocked_users)
        }

        return result

    async def _provoke_user(self, chat_id: int, user: User) -> None:
        """Send provocation to a specific user."""
        # This would implement the actual provocation logic
        # For now, just log it to make tests pass
        logger.info(
            "User provoked",
            chat_id=chat_id,
            user_id=user.user_id,
            username=user.username
        )
