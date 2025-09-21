"""Modlog notification system for failed challenges."""

import os

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

from ..config.loader import ConfigLoader
from .tracker import ProvocationTracker

logger = structlog.get_logger(__name__)


class ModlogNotifier:
    """Sends notifications to modlog channels for failed challenges."""

    def __init__(
        self, tracker: ProvocationTracker | None = None, config_loader: ConfigLoader | None = None
    ) -> None:
        """Initialize modlog notifier.

        Dependencies are lazily instantiated to support test patching.
        """
        self.tracker = tracker
        self.config_loader = config_loader

    async def schedule_kick_notification(self, provocation_id: int) -> None:
        """Send kick notification to linked modlog channel."""
        # Resolve dependencies lazily to honor runtime patches
        tracker = self.tracker or ProvocationTracker()
        config_loader = self.config_loader or ConfigLoader()

        # Get provocation details
        provocation = await tracker.get_provocation(provocation_id)
        if not provocation:
            logger.error("Provocation not found", provocation_id=provocation_id)
            return

        # Load configuration to find linked modlog
        global_config, channels_config, puzzles_config = config_loader.load_all()
        modlog_channel = channels_config.get_linked_modlog(provocation.chat_id)

        if not modlog_channel:
            logger.warning(
                "No linked modlog found for chat",
                chat_id=provocation.chat_id,
                provocation_id=provocation_id,
            )
            return

        # Compose notification message
        message_text = (
            f"⚠️ **Challenge Failed - Manual Action Required**\n\n"
            f"**User:** {provocation.user_id}\n"
            f"**Chat:** {provocation.chat_id}\n"
            f"**Reason:** Failed to answer challenge correctly\n"
            f"**Date:** {provocation.provocation_date.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"**Action Required:** Please kick this user using Telegram admin tools.\n"
            f"Use: `/kick {provocation.user_id}` or via user profile.\n\n"
            f"Click 'Confirm Kick' after manually removing the user."
        )

        # Create confirmation keyboard
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Confirm Kick", callback_data=f"kick_confirm_{provocation_id}"
                    ),
                    InlineKeyboardButton(
                        "📝 Add Note", callback_data=f"kick_note_{provocation_id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "❌ Dismiss", callback_data=f"kick_dismiss_{provocation_id}"
                    )
                ],
            ]
        )

        # Send notification
        bot_token = os.environ.get("TELEGRAM_TOKEN")
        if not bot_token:
            logger.error("TELEGRAM_TOKEN not found")
            return

        app = Application.builder().token(bot_token).build()

        try:
            await app.bot.send_message(
                chat_id=modlog_channel.chat_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            logger.info(
                "Kick notification sent",
                provocation_id=provocation_id,
                modlog_chat_id=modlog_channel.chat_id,
                user_id=provocation.user_id,
            )

        except Exception as e:
            logger.error(
                "Failed to send kick notification",
                provocation_id=provocation_id,
                modlog_chat_id=modlog_channel.chat_id,
                error=str(e),
            )

    async def handle_kick_confirmation(
        self, provocation_id: int, admin_user_id: int, action: str
    ) -> None:
        """Handle kick confirmation callback."""
        tracker = self.tracker or ProvocationTracker()
        provocation = await tracker.get_provocation(provocation_id)
        if not provocation:
            return

        if action == "confirm":
            # Mark as manually handled
            await tracker.update_provocation_status(provocation_id, "manually_kicked")
            logger.info(
                "Kick confirmed by admin",
                provocation_id=provocation_id,
                admin_user_id=admin_user_id,
            )

        elif action == "dismiss":
            # Mark as dismissed
            await tracker.update_provocation_status(provocation_id, "dismissed")
            logger.info(
                "Kick dismissed by admin",
                provocation_id=provocation_id,
                admin_user_id=admin_user_id,
            )
