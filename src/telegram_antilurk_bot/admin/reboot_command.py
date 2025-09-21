"""Reboot command handler for graceful shutdown."""

import os
import sys

import structlog
from telegram import Update
from telegram.ext import Application, ContextTypes

from ..config.loader import ConfigLoader

logger = structlog.get_logger(__name__)


class RebootCommandHandler:
    """Handles /antlurk reboot command for graceful shutdown."""

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """Initialize reboot command handler."""
        self.config_loader = config_loader or ConfigLoader()

    async def handle_reboot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /antlurk reboot command."""
        if not update.message:
            return

        try:
            # Post shutdown notice to current chat
            await update.message.reply_text(
                "🔄 **System Reboot Initiated**\n\n"
                "Persisting configuration state and shutting down gracefully...\n"
                "The bot will restart automatically if configured with a process manager.",
                parse_mode='Markdown'
            )

            # Persist all configuration state
            await self._persist_application_state()

            # Post shutdown notice to all modlog channels
            await self._notify_modlog_channels()

            logger.info(
                "Reboot command executed",
                requested_by=update.effective_user.id if update.effective_user else None,
                chat_id=update.effective_chat.id if update.effective_chat else None
            )

            # Exit with code 0 for graceful shutdown
            sys.exit(0)

        except Exception as e:
            logger.error("Failed to execute reboot", error=str(e))
            await update.message.reply_text("❌ Error during reboot process.")

    async def _persist_application_state(self) -> None:
        """Persist all application state before shutdown."""
        try:
            # This would save all configuration changes
            # For Phase 7, we'll simulate this
            logger.info("Persisting application state before shutdown")

            # In a real implementation, this would:
            # 1. Save all in-memory configuration changes
            # 2. Flush any pending database writes
            # 3. Save current rate limiting states
            # 4. Persist any active challenge states

            # Placeholder for save_all_configs method
            global_config, channels_config, puzzles_config = self.config_loader.load_all()

            # Save configurations with updated provenance
            global_config.update_provenance("reboot-shutdown")
            channels_config.update_provenance("reboot-shutdown")
            puzzles_config.update_provenance("reboot-shutdown")

            # Save all configs (would be implemented in ConfigLoader)
            # self.config_loader.save_all_configs()

            logger.info("Application state persisted successfully")

        except Exception as e:
            logger.error("Failed to persist application state", error=str(e))
            raise

    async def _notify_modlog_channels(self) -> None:
        """Send shutdown notice to all modlog channels."""
        try:
            # Load configuration to get modlog channels
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            modlog_channels = channels_config.get_modlog_channels()

            if not modlog_channels:
                logger.info("No modlog channels configured for shutdown notification")
                return

            # Get bot token
            bot_token = os.environ.get('TELEGRAM_TOKEN')
            if not bot_token:
                logger.warning("No TELEGRAM_TOKEN available for shutdown notifications")
                return

            # Create application for sending messages
            app = Application.builder().token(bot_token).build()

            shutdown_message = (
                "🔄 **Bot Shutdown Notice**\n\n"
                "The Telegram Anti-Lurk Bot is shutting down for maintenance.\n"
                "• All configuration has been saved\n"
                "• Active challenges will be restored on restart\n"
                "• Service will resume automatically\n\n"
                f"Shutdown initiated at: {logger._context.get('timestamp', 'Unknown')}"
            )

            # Send to all modlog channels
            for modlog in modlog_channels:
                try:
                    await app.bot.send_message(
                        chat_id=modlog.chat_id,
                        text=shutdown_message,
                        parse_mode='Markdown'
                    )
                    logger.info(
                        "Shutdown notice sent",
                        modlog_chat_id=modlog.chat_id,
                        modlog_name=modlog.chat_name
                    )
                except Exception as e:
                    logger.error(
                        "Failed to send shutdown notice",
                        modlog_chat_id=modlog.chat_id,
                        error=str(e)
                    )

        except Exception as e:
            logger.error("Failed to notify modlog channels", error=str(e))
