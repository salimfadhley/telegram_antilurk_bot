"""Unlink command handler for removing chat connections."""

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from ..config.loader import ConfigLoader

logger = structlog.get_logger(__name__)


class UnlinkCommandHandler:
    """Handles /antlurk unlink command for removing chat links."""

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """Initialize unlink command handler."""
        self.config_loader = config_loader or ConfigLoader()

    async def handle_unlink_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /antlurk unlink <chat_id> command."""
        if not update.message or not context.args:
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: `/antlurk unlink <chat_id>`\n\n"
                    "Example: `/antlurk unlink -1009876543210`",
                    parse_mode="Markdown",
                )
            return

        # Parse chat ID argument
        try:
            target_chat_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid chat ID format. Must be a negative integer."
            )
            return

        try:
            # Load current configuration
            global_config, channels_config, puzzles_config = self.config_loader.load_all()

            # Find and unlink the connection
            unlink_performed = False
            affected_chat_name = None

            for channel in channels_config.channels:
                if channel.modlog_ref == target_chat_id:
                    # This is a moderated chat linked to the target modlog
                    affected_chat_name = channel.chat_name
                    channel.modlog_ref = None
                    unlink_performed = True
                    logger.info(
                        "Unlinked moderated chat from modlog",
                        moderated_chat=channel.chat_id,
                        modlog_chat=target_chat_id,
                    )
                    break

            if not unlink_performed:
                # Check if target is a moderated chat linked to something
                target_channel = next(
                    (ch for ch in channels_config.channels if ch.chat_id == target_chat_id), None
                )
                if target_channel and target_channel.modlog_ref:
                    affected_chat_name = target_channel.chat_name
                    target_channel.modlog_ref = None
                    unlink_performed = True
                    logger.info(
                        "Unlinked moderated chat",
                        moderated_chat=target_chat_id,
                        was_linked_to=target_channel.modlog_ref,
                    )

            if not unlink_performed:
                await update.message.reply_text(
                    f"❌ No active link found involving chat ID `{target_chat_id}`.",
                    parse_mode="Markdown",
                )
                return

            # Save the updated configuration
            self.config_loader.save_channels_config(channels_config)

            # Generate new linking message for the affected chat
            new_link_code = self._generate_link_code()

            success_text = "✅ **Unlink Successful**\n\n"
            success_text += (
                f"Chat `{affected_chat_name}` has been unlinked from `{target_chat_id}`.\n\n"
            )
            success_text += f"**New Link Code: `{new_link_code}`**\n\n"
            success_text += (
                "To re-establish connections, use this code in the linking handshake process."
            )

            await update.message.reply_text(success_text, parse_mode="Markdown")

        except Exception as e:
            logger.error("Failed to unlink chat", target_chat_id=target_chat_id, error=str(e))
            await update.message.reply_text("❌ Error performing unlink operation.")

    def _generate_link_code(self) -> str:
        """Generate a new link code for re-linking."""
        import random
        import string

        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
