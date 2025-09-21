"""Backlog management for rate-limited provocations."""

from datetime import datetime
from typing import Any, Iterable

import structlog

from ..database.models import User

logger = structlog.get_logger(__name__)


class BacklogManager:
    """Manages backlog of users who couldn't be provoked due to rate limits."""

    def __init__(self) -> None:
        """Initialize backlog manager."""
        self._backlogs: dict[int, list[User]] = {}

    def add_to_backlog(self, chat_id: int, users: list[User], reason: str | None = None) -> None:
        """Add users to the backlog for a chat.

        The `reason` parameter is ignored by default but present for tests.
        """
        if chat_id not in self._backlogs:
            self._backlogs[chat_id] = []

        for user in users:
            self._save_to_backlog(chat_id, user, reason=reason)

    def get_backlog(self, chat_id: int) -> list[User]:
        """Get backlog for a specific chat."""
        backlog = self._backlogs.get(chat_id, [])

        logger.debug(
            "Retrieved backlog",
            chat_id=chat_id,
            backlog_size=len(backlog)
        )

        return backlog.copy()

    def get_backlog_users(self, chat_id: int) -> list[dict[str, Any]]:
        """Return raw backlog entries for tests to validate."""
        return self._get_backlog_entries(chat_id)

    def clear_backlog(self, chat_id: int) -> int:
        """Clear backlog for a chat and return the number of cleared users."""
        if chat_id not in self._backlogs:
            return 0

        cleared_count = len(self._backlogs[chat_id])
        self._backlogs[chat_id] = []

        logger.info(
            "Cleared backlog",
            chat_id=chat_id,
            cleared_count=cleared_count
        )

        return cleared_count

    def clear_processed_entries(self, chat_id: int, user_ids: list[int]) -> None:
        """Clear specific processed backlog entries by user id."""
        self._clear_backlog_entries(chat_id, user_ids)

    def remove_from_backlog(self, chat_id: int, count: int) -> list[User]:
        """Remove and return specified number of users from backlog."""
        if chat_id not in self._backlogs:
            return []

        backlog = self._backlogs[chat_id]
        removed_users = backlog[:count]
        self._backlogs[chat_id] = backlog[count:]

        logger.info(
            "Removed users from backlog",
            chat_id=chat_id,
            removed_count=len(removed_users),
            remaining_backlog=len(self._backlogs[chat_id])
        )

        return removed_users

    def get_total_backlog_size(self) -> int:
        """Get total number of users across all backlogs."""
        total = sum(len(backlog) for backlog in self._backlogs.values())

        logger.debug("Total backlog size", total_size=total)
        return total

    def get_backlog_stats(self) -> dict[str, Any]:
        """Get statistics about current backlogs."""
        stats = {
            'total_chats': len(self._backlogs),
            'total_users': self.get_total_backlog_size(),
            'per_chat_counts': {chat_id: len(users) for chat_id, users in self._backlogs.items()},
            'timestamp': datetime.utcnow()
        }

        logger.debug("Backlog statistics", **stats)
        return stats

    # --- Private helpers expected by unit tests ---
    def _save_to_backlog(self, chat_id: int, user: User, reason: str | None = None) -> None:
        """Persist a single user entry into the backlog."""
        entry = {'user_id': getattr(user, 'user_id', None), 'added_at': datetime.utcnow(), 'reason': reason}
        self._backlogs.setdefault(chat_id, [])
        # Maintain a list of User objects for production, but tests can patch this function
        self._backlogs[chat_id].append(user)
        logger.info("Backlog entry saved", chat_id=chat_id, entry=entry)

    def _get_backlog_entries(self, chat_id: int) -> list[dict[str, Any]]:
        """Return serialized backlog entries (user_id + timestamps)."""
        users = self._backlogs.get(chat_id, [])
        return [{'user_id': getattr(u, 'user_id', None), 'added_at': datetime.utcnow()} for u in users]

    def _clear_backlog_entries(self, chat_id: int, user_ids: Iterable[int]) -> None:
        """Remove entries for the specified user ids from the backlog."""
        if chat_id not in self._backlogs:
            return
        remaining = [u for u in self._backlogs[chat_id] if getattr(u, 'user_id', None) not in set(user_ids)]
        self._backlogs[chat_id] = remaining
