"""Provocation lifecycle logging and history tracking."""

from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ProvocationLogger:
    """Logs provocation lifecycle events for history and rate limiting."""

    def __init__(self) -> None:
        """Initialize provocation logger."""
        # In-memory storage for Phase 6 - will be replaced with database in Phase 2
        self._provocation_history: dict[int, list[dict[str, Any]]] = {}
        self._provocation_events: list[dict[str, Any]] = []

    async def log_provocation_created(
        self,
        provocation_id: int,
        chat_id: int,
        user_id: int,
        puzzle_id: str,
        created_at: datetime | None = None,
        expires_at: datetime | None = None
    ) -> None:
        """Log provocation creation event."""
        if created_at is None:
            created_at = datetime.utcnow()

        event = {
            'event': 'created',
            'provocation_id': provocation_id,
            'chat_id': chat_id,
            'user_id': user_id,
            'puzzle_id': puzzle_id,
            'timestamp': created_at,
            'expires_at': expires_at
        }

        # Add to history
        if provocation_id not in self._provocation_history:
            self._provocation_history[provocation_id] = []
        self._provocation_history[provocation_id].append(event)

        # Add to global events list
        self._provocation_events.append(event)

        logger.info(
            "Provocation creation logged",
            provocation_id=provocation_id,
            chat_id=chat_id,
            user_id=user_id,
            puzzle_id=puzzle_id
        )

    async def log_provocation_response(
        self,
        provocation_id: int,
        user_id: int,
        response_time: datetime | None = None,
        choice_selected: int | None = None,
        is_correct: bool | None = None
    ) -> None:
        """Log user response to provocation."""
        if response_time is None:
            response_time = datetime.utcnow()

        event = {
            'event': 'response',
            'provocation_id': provocation_id,
            'user_id': user_id,
            'timestamp': response_time,
            'choice_selected': choice_selected,
            'is_correct': is_correct
        }

        # Add to history
        if provocation_id not in self._provocation_history:
            self._provocation_history[provocation_id] = []
        self._provocation_history[provocation_id].append(event)

        # Add to global events list
        self._provocation_events.append(event)

        logger.info(
            "Provocation response logged",
            provocation_id=provocation_id,
            user_id=user_id,
            is_correct=is_correct
        )

    async def log_provocation_expired(
        self,
        provocation_id: int,
        expired_at: datetime | None = None,
        final_status: str = "expired"
    ) -> None:
        """Log provocation expiration event."""
        if expired_at is None:
            expired_at = datetime.utcnow()

        event = {
            'event': 'expired',
            'provocation_id': provocation_id,
            'timestamp': expired_at,
            'final_status': final_status
        }

        # Add to history
        if provocation_id not in self._provocation_history:
            self._provocation_history[provocation_id] = []
        self._provocation_history[provocation_id].append(event)

        # Add to global events list
        self._provocation_events.append(event)

        logger.info(
            "Provocation expiration logged",
            provocation_id=provocation_id,
            final_status=final_status
        )

    async def get_provocation_history(self, provocation_id: int) -> list[dict[str, Any]]:
        """Get complete history for a provocation."""
        return self._provocation_history.get(provocation_id, [])

    async def get_provocation_count_since(
        self,
        chat_id: int,
        since: datetime
    ) -> int:
        """Get count of provocations created since a given time for rate limiting."""
        count = 0
        for event in self._provocation_events:
            if (event['event'] == 'created' and
                event['chat_id'] == chat_id and
                event['timestamp'] >= since):
                count += 1

        logger.debug(
            "Provocation count calculated",
            chat_id=chat_id,
            since=since,
            count=count
        )

        return count

    async def get_recent_provocations(
        self,
        chat_id: int | None = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get recent provocation events."""
        events = self._provocation_events.copy()

        if chat_id is not None:
            events = [e for e in events if e.get('chat_id') == chat_id]

        # Sort by timestamp descending
        events.sort(key=lambda x: x['timestamp'], reverse=True)

        return events[:limit]

    async def get_user_provocation_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get provocation history for a specific user."""
        user_events = [
            event for event in self._provocation_events
            if event.get('user_id') == user_id
        ]

        # Sort by timestamp descending
        user_events.sort(key=lambda x: x['timestamp'], reverse=True)

        return user_events[:limit]
