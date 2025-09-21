"""Complete lifecycle logger for provocation events."""

from datetime import datetime
from typing import Any

import structlog

from .provocation_logger import ProvocationLogger

logger = structlog.get_logger(__name__)


class LifecycleLogger:
    """Comprehensive lifecycle logger for provocation workflow."""

    def __init__(self) -> None:
        """Initialize lifecycle logger."""
        self.provocation_logger = ProvocationLogger()
        # Additional lifecycle events not covered by provocation logger
        self._additional_events: list[dict[str, Any]] = []

    async def log_provocation_created(
        self,
        provocation_id: int,
        chat_id: int,
        user_id: int,
        puzzle_id: str
    ) -> None:
        """Log provocation creation."""
        await self.provocation_logger.log_provocation_created(
            provocation_id=provocation_id,
            chat_id=chat_id,
            user_id=user_id,
            puzzle_id=puzzle_id
        )

    async def log_provocation_response(
        self,
        provocation_id: int,
        user_id: int,
        is_correct: bool
    ) -> None:
        """Log provocation response."""
        await self.provocation_logger.log_provocation_response(
            provocation_id=provocation_id,
            user_id=user_id,
            is_correct=is_correct
        )

    async def log_modlog_notification_sent(
        self,
        provocation_id: int,
        modlog_chat_id: int
    ) -> None:
        """Log when modlog notification is sent."""
        event = {
            'event': 'modlog_notified',
            'provocation_id': provocation_id,
            'modlog_chat_id': modlog_chat_id,
            'timestamp': datetime.now(datetime.UTC)
        }

        self._additional_events.append(event)

        logger.info(
            "Modlog notification logged",
            provocation_id=provocation_id,
            modlog_chat_id=modlog_chat_id
        )

    async def log_manual_kick_confirmed(
        self,
        provocation_id: int,
        admin_user_id: int,
        confirmation_timestamp: datetime | None = None
    ) -> None:
        """Log when admin confirms manual kick."""
        if confirmation_timestamp is None:
            confirmation_timestamp = datetime.now(datetime.UTC)

        event = {
            'event': 'kick_confirmed',
            'provocation_id': provocation_id,
            'admin_user_id': admin_user_id,
            'timestamp': confirmation_timestamp
        }

        self._additional_events.append(event)

        logger.info(
            "Manual kick confirmation logged",
            provocation_id=provocation_id,
            admin_user_id=admin_user_id
        )

    async def log_kick_dismissed(
        self,
        provocation_id: int,
        admin_user_id: int,
        dismissal_reason: str | None = None
    ) -> None:
        """Log when admin dismisses kick recommendation."""
        event = {
            'event': 'kick_dismissed',
            'provocation_id': provocation_id,
            'admin_user_id': admin_user_id,
            'dismissal_reason': dismissal_reason,
            'timestamp': datetime.now(datetime.UTC)
        }

        self._additional_events.append(event)

        logger.info(
            "Kick dismissal logged",
            provocation_id=provocation_id,
            admin_user_id=admin_user_id,
            reason=dismissal_reason
        )

    async def get_complete_history(self, provocation_id: int) -> list[dict[str, Any]]:
        """Get complete lifecycle history for a provocation."""
        # Get base provocation events
        base_history = await self.provocation_logger.get_provocation_history(provocation_id)

        # Add additional lifecycle events
        additional_events = [
            event for event in self._additional_events
            if event['provocation_id'] == provocation_id
        ]

        # Combine and sort by timestamp
        complete_history = base_history + additional_events
        complete_history.sort(key=lambda x: x['timestamp'])

        logger.debug(
            "Complete provocation history retrieved",
            provocation_id=provocation_id,
            total_events=len(complete_history)
        )

        return complete_history

    async def get_lifecycle_stats(self) -> dict[str, Any]:
        """Get statistics about provocation lifecycles."""
        # Get stats from provocation logger
        all_additional_events = self._additional_events

        modlog_notifications = len([
            e for e in all_additional_events
            if e['event'] == 'modlog_notified'
        ])

        kick_confirmations = len([
            e for e in all_additional_events
            if e['event'] == 'kick_confirmed'
        ])

        kick_dismissals = len([
            e for e in all_additional_events
            if e['event'] == 'kick_dismissed'
        ])

        stats = {
            'modlog_notifications_sent': modlog_notifications,
            'manual_kicks_confirmed': kick_confirmations,
            'kicks_dismissed': kick_dismissals,
            'total_additional_events': len(all_additional_events)
        }

        logger.debug("Lifecycle statistics calculated", **stats)
        return stats
