"""Main message processor coordinating all logging components."""

from typing import Any

import structlog
from telegram import Update

from .message_archiver import MessageArchiver
from .nats_publisher import NATSEventPublisher
from .user_tracker import UserTracker

logger = structlog.get_logger(__name__)


class MessageProcessor:
    """Main processor for handling message logging workflow."""

    def __init__(self) -> None:
        """Initialize message processor."""
        self.archiver = MessageArchiver()
        self.user_tracker = UserTracker()
        self.nats_publisher = NATSEventPublisher()

    async def process_message(self, update: Update) -> bool:
        """Process incoming message through all logging components."""
        if not update.message or not update.message.from_user:
            return False

        try:
            # Archive the message
            archived_message = await self.archiver.archive_message(update)

            if archived_message is None:
                # Message was filtered out (bot message, non-moderated chat, etc.)
                return False

            # Update user activity tracking (already done in archiver)
            # This is a no-op but shows the intended flow
            await self.user_tracker.update_user_activity(
                user_id=update.message.from_user.id,
                chat_id=update.message.chat.id,
                timestamp=update.message.date,
                telegram_user=update.message.from_user
            )

            # Publish to NATS if enabled
            await self.nats_publisher.publish_event('message.received', {
                'event_type': 'message_received',
                'chat_id': update.message.chat.id,
                'user_id': update.message.from_user.id,
                'message_id': update.message.message_id,
                'message_type': archived_message.message_type,
                'timestamp': update.message.date.isoformat()
            })

            logger.info(
                "Message processed successfully",
                message_id=update.message.message_id,
                chat_id=update.message.chat.id,
                user_id=update.message.from_user.id
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to process message",
                message_id=getattr(update.message, 'message_id', None),
                error=str(e)
            )
            return False

    async def get_processing_stats(self) -> dict[str, Any]:
        """Get statistics about message processing."""
        user_stats = await self.user_tracker.get_user_stats()

        stats = {
            'total_archived_messages': len(self.archiver._message_archive),
            'nats_enabled': self.nats_publisher.enabled,
            **user_stats
        }

        return stats
