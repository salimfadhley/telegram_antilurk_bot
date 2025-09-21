"""Database view updater for user_channel_activity statistics."""

from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ViewUpdater:
    """Updates and maintains the user_channel_activity database view."""

    def __init__(self) -> None:
        """Initialize view updater."""
        # In-memory storage for Phase 6 - will be replaced with database view in Phase 2
        self._activity_records: list[dict[str, Any]] = []

    async def record_user_activity(self, user_id: int, chat_id: int, timestamp: datetime) -> None:
        """Record user activity for view aggregation."""
        activity_record = {
            "user_id": user_id,
            "chat_id": chat_id,
            "timestamp": timestamp,
            "recorded_at": datetime.utcnow(),
        }

        self._activity_records.append(activity_record)

        logger.debug(
            "User activity recorded", user_id=user_id, chat_id=chat_id, timestamp=timestamp
        )

    async def get_user_channel_activity(self, user_id: int, chat_id: int) -> dict[str, Any] | None:
        """Get aggregated activity stats for user in specific channel."""
        user_records = [
            record
            for record in self._activity_records
            if record["user_id"] == user_id and record["chat_id"] == chat_id
        ]

        if not user_records:
            return None

        # Calculate aggregated statistics
        message_count = len(user_records)
        timestamps = [record["timestamp"] for record in user_records]

        first_message = min(timestamps)
        last_message = max(timestamps)

        activity_stats = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message_count": message_count,
            "first_message_at": first_message,
            "last_message_at": last_message,
            "days_active": (last_message - first_message).days + 1
            if first_message != last_message
            else 1,
        }

        logger.debug("User channel activity calculated", **activity_stats)

        return activity_stats

    async def get_chat_activity_summary(self, chat_id: int) -> dict[str, Any]:
        """Get activity summary for entire chat."""
        chat_records = [record for record in self._activity_records if record["chat_id"] == chat_id]

        if not chat_records:
            return {
                "chat_id": chat_id,
                "total_messages": 0,
                "unique_users": 0,
                "first_activity": None,
                "last_activity": None,
            }

        unique_users = {record["user_id"] for record in chat_records}
        timestamps = [record["timestamp"] for record in chat_records]

        summary = {
            "chat_id": chat_id,
            "total_messages": len(chat_records),
            "unique_users": len(unique_users),
            "first_activity": min(timestamps),
            "last_activity": max(timestamps),
        }

        logger.debug("Chat activity summary calculated", chat_id=chat_id, **summary)
        return summary

    async def refresh_view(self) -> dict[str, Any]:
        """Refresh the user_channel_activity view (placeholder for database operation)."""
        # In a real implementation, this would refresh the database materialized view
        # For Phase 6, we just return current statistics

        total_records = len(self._activity_records)
        unique_users = len({record["user_id"] for record in self._activity_records})
        unique_chats = len({record["chat_id"] for record in self._activity_records})

        refresh_stats = {
            "total_activity_records": total_records,
            "unique_users": unique_users,
            "unique_chats": unique_chats,
            "refresh_timestamp": datetime.utcnow(),
        }

        logger.info("Activity view refreshed", **refresh_stats)
        return refresh_stats
