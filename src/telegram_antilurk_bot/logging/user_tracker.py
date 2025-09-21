"""User activity tracking for last interaction timestamps."""

from datetime import datetime
from typing import Any

import structlog

from ..database.models import User

logger = structlog.get_logger(__name__)


class UserTracker:
    """Tracks user activity and maintains last interaction timestamps."""

    def __init__(self) -> None:
        """Initialize user tracker."""
        # In-memory storage for Phase 6 - will be replaced with database in Phase 2
        self._users: dict[int, User] = {}

    async def update_user_activity(
        self,
        user_id: int,
        chat_id: int,
        timestamp: datetime,
        telegram_user: Any | None = None
    ) -> User:
        """Update or create user activity record."""
        existing_user = self._users.get(user_id)

        if existing_user:
            # Update existing user
            existing_user.last_message_at = timestamp
            user = existing_user
            logger.debug(
                "Updated user activity",
                user_id=user_id,
                chat_id=chat_id,
                timestamp=timestamp
            )
        else:
            # Create new user record
            user = User(
                user_id=user_id,
                username=getattr(telegram_user, 'username', None) if telegram_user else None,
                first_name=getattr(telegram_user, 'first_name', None) if telegram_user else None,
                last_name=getattr(telegram_user, 'last_name', None) if telegram_user else None,
                last_message_at=timestamp,
                join_date=timestamp,
                is_bot=getattr(telegram_user, 'is_bot', False) if telegram_user else False,
                is_admin=False  # Will be determined separately
            )
            self._users[user_id] = user

            logger.info(
                "Created new user record",
                user_id=user_id,
                username=user.username,
                join_date=timestamp
            )

        return user

    async def track_user_activity(
        self,
        user_id: int,
        chat_id: int,
        timestamp: datetime,
        telegram_user: Any | None = None
    ) -> User:
        """Contract alias for updating user activity.

        Maintains backwards-compatibility with tests expecting a
        `track_user_activity` API while delegating to the main
        `update_user_activity` implementation.
        """
        return await self.update_user_activity(
            user_id=user_id,
            chat_id=chat_id,
            timestamp=timestamp,
            telegram_user=telegram_user,
        )

    async def get_user(self, user_id: int) -> User | None:
        """Get user by ID."""
        return self._users.get(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        for user in self._users.values():
            if user.username and user.username.lower() == username.lower():
                return user
        return None

    async def get_users_by_activity(
        self,
        chat_id: int,
        since: datetime | None = None
    ) -> list[User]:
        """Get users who have been active since a given time."""
        users = []
        for user in self._users.values():
            if since and user.last_message_at and user.last_message_at >= since:
                users.append(user)
            elif since is None:
                users.append(user)

        return users

    async def get_inactive_users(
        self,
        chat_id: int,
        inactive_since: datetime
    ) -> list[User]:
        """Get users who haven't been active since a given time."""
        inactive_users = []
        for user in self._users.values():
            if (user.last_message_at is None or
                user.last_message_at < inactive_since):
                inactive_users.append(user)

        return inactive_users

    async def mark_user_as_admin(self, user_id: int) -> bool:
        """Mark user as admin."""
        user = self._users.get(user_id)
        if user:
            user.is_admin = True
            logger.info("User marked as admin", user_id=user_id)
            return True
        return False

    async def get_user_stats(self) -> dict[str, Any]:
        """Get overall user statistics."""
        total_users = len(self._users)
        active_users = len([
            user for user in self._users.values()
            if user.last_message_at is not None
        ])
        admin_users = len([
            user for user in self._users.values()
            if user.is_admin
        ])

        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'inactive_users': total_users - active_users
        }

        logger.debug("User statistics", **stats)
        return stats
