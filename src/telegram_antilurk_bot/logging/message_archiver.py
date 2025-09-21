"""Message archiving functionality for storing chat messages."""

from typing import Any

import structlog
from telegram import Update

from ..config.loader import ConfigLoader
from ..database.models import MessageArchive
from .user_tracker import UserTracker

logger = structlog.get_logger(__name__)


class MessageArchiver:
    """Archives messages from moderated chats to the database."""

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """Initialize message archiver."""
        self.config_loader = config_loader or ConfigLoader()
        self.user_tracker = UserTracker()
        # In-memory storage for Phase 6 - will be replaced with database in Phase 2
        self._message_archive: list[MessageArchive] = []
        self._next_archive_id = 1

    async def archive_message(self, update: Update) -> MessageArchive | None:
        """Archive a message if it meets archiving criteria."""
        if not update.message or not update.message.from_user:
            return None

        # Skip bot messages
        if update.message.from_user.is_bot:
            logger.debug("Skipping bot message", user_id=update.message.from_user.id)
            return None

        # Check if chat is moderated
        if not await self._is_moderated_chat(update.message.chat.id):
            logger.debug("Skipping non-moderated chat", chat_id=update.message.chat.id)
            return None

        # Determine message type and content
        message_type, message_text = self._extract_message_content(update.message)

        # Create archive entry
        archive_entry = MessageArchive(
            message_id=update.message.message_id,
            chat_id=update.message.chat.id,
            user_id=update.message.from_user.id,
            message_text=message_text,
            message_date=update.message.date,
            message_type=message_type
        )

        # Store in archive (placeholder for database)
        self._message_archive.append(archive_entry)

        # Update user activity tracking
        await self.user_tracker.update_user_activity(
            user_id=update.message.from_user.id,
            chat_id=update.message.chat.id,
            timestamp=update.message.date,
            telegram_user=update.message.from_user
        )

        logger.info(
            "Message archived",
            message_id=update.message.message_id,
            chat_id=update.message.chat.id,
            user_id=update.message.from_user.id,
            message_type=message_type
        )

        return archive_entry

    async def _is_moderated_chat(self, chat_id: int) -> bool:
        """Check if chat is configured as moderated."""
        try:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            moderated_channels = channels_config.get_moderated_channels()
            return any(channel.chat_id == chat_id for channel in moderated_channels)
        except Exception as e:
            logger.error("Error checking moderated chat status", chat_id=chat_id, error=str(e))
            return False

    def _extract_message_content(self, message: Any) -> tuple[str, str | None]:
        """Extract message type and text content from Telegram message."""
        if message.text:
            return "text", message.text
        elif message.photo:
            return "photo", message.caption
        elif message.sticker:
            return "sticker", getattr(message.sticker, 'emoji', None)
        elif message.document:
            return "document", message.caption
        elif message.video:
            return "video", message.caption
        elif message.voice:
            return "voice", None
        elif message.audio:
            return "audio", message.caption
        elif message.animation:
            return "animation", message.caption
        else:
            return "other", None

    async def get_recent_messages(self, chat_id: int, limit: int = 100) -> list[MessageArchive]:
        """Get recent messages from a chat."""
        chat_messages = [
            msg for msg in self._message_archive
            if msg.chat_id == chat_id
        ]
        # Sort by date descending and limit
        chat_messages.sort(key=lambda x: x.message_date, reverse=True)
        return chat_messages[:limit]

    async def get_user_message_count(self, user_id: int, chat_id: int) -> int:
        """Get count of messages from user in specific chat."""
        return len([
            msg for msg in self._message_archive
            if msg.user_id == user_id and msg.chat_id == chat_id
        ])
