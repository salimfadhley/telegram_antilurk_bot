"""Permission validation for admin commands."""

import os

import structlog
from telegram import Update
from telegram.ext import Application

from ..config.loader import ConfigLoader
from ..logging.user_tracker import UserTracker

logger = structlog.get_logger(__name__)


class PermissionValidator:
    """Validates permissions for admin commands."""

    def __init__(self) -> None:
        """Initialize permission validator."""
        self.config_loader = ConfigLoader()
        self.user_tracker = UserTracker()

    async def validate_admin_permission(self, update: Update) -> bool:
        """Validate that user has admin permissions."""
        if not update.effective_user or not update.message:
            return False

        user_id = update.effective_user.id

        try:
            # Check if user is marked as admin in our system
            user = await self.user_tracker.get_user(user_id)
            if user and user.is_admin:
                return True

            # Check if user is Telegram chat admin
            if await self.validate_telegram_admin(update):
                # Mark user as admin in our system for future checks
                await self.user_tracker.mark_user_as_admin(user_id)
                return True

            # User is not admin
            await update.message.reply_text(
                "❌ This command requires administrator permissions."
            )
            return False

        except Exception as e:
            logger.error("Failed to validate admin permission", user_id=user_id, error=str(e))
            return False

    async def validate_telegram_admin(self, update: Update) -> bool:
        """Validate admin status using Telegram chat admin API."""
        if not update.effective_user or not update.effective_chat:
            return False

        try:
            bot_token = os.environ.get('TELEGRAM_TOKEN')
            if not bot_token:
                return False

            app = Application.builder().token(bot_token).build()

            chat_member = await app.bot.get_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id
            )

            # Check if user is admin or creator
            admin_statuses = ['administrator', 'creator']
            is_admin = chat_member.status in admin_statuses

            logger.debug(
                "Telegram admin validation",
                user_id=update.effective_user.id,
                chat_id=update.effective_chat.id,
                status=chat_member.status,
                is_admin=is_admin
            )

            return is_admin

        except Exception as e:
            logger.error(
                "Failed to validate Telegram admin status",
                user_id=update.effective_user.id if update.effective_user else None,
                chat_id=update.effective_chat.id if update.effective_chat else None,
                error=str(e)
            )
            return False

    async def validate_moderated_chat(self, update: Update) -> bool:
        """Validate that command is being used in a moderated chat."""
        if not update.effective_chat or not update.message:
            return False

        try:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            moderated_channels = channels_config.get_moderated_channels()

            chat_id = update.effective_chat.id
            is_moderated = any(channel.chat_id == chat_id for channel in moderated_channels)

            if not is_moderated:
                await update.message.reply_text(
                    "❌ This command can only be used in moderated chats."
                )
                return False

            return True

        except Exception as e:
            logger.error("Failed to validate moderated chat", error=str(e))
            return False

    async def validate_command_permissions(
        self,
        update: Update,
        require_admin: bool = True,
        require_moderated_chat: bool = False
    ) -> bool:
        """Combined permission validation for commands."""
        if require_admin:
            if not await self.validate_admin_permission(update):
                return False

        if require_moderated_chat:
            if not await self.validate_moderated_chat(update):
                return False

        return True
