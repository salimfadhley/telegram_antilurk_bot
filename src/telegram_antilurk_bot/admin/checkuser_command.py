"""Check user command handler for user activity lookup."""

from datetime import datetime

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from ..logging.message_archiver import MessageArchiver
from ..logging.user_tracker import UserTracker

logger = structlog.get_logger(__name__)


class CheckUserCommandHandler:
    """Handles /antlurk checkuser command for user activity lookup."""

    def __init__(
        self,
        user_tracker: UserTracker | None = None,
        message_archiver: MessageArchiver | None = None,
    ) -> None:
        """Initialize checkuser command handler."""
        self.user_tracker = user_tracker or UserTracker()
        self.message_archiver = message_archiver or MessageArchiver()

    async def handle_checkuser_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /antlurk checkuser <username|user_id> command."""
        if not update.message or not context.args:
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: `/antlurk checkuser <username|user_id>`\n\n"
                    "Examples:\n"
                    "• `/antlurk checkuser @username`\n"
                    "• `/antlurk checkuser 123456789`",
                    parse_mode="Markdown",
                )
            return

        user_identifier = context.args[0]

        try:
            # Determine if input is username or user ID
            user = None
            if user_identifier.startswith("@"):
                # Username lookup
                username = user_identifier[1:]  # Remove @ prefix
                user = await self.user_tracker.get_user_by_username(username)
            else:
                # Try to parse as user ID
                try:
                    user_id = int(user_identifier)
                    user = await self.user_tracker.get_user(user_id)
                except ValueError:
                    await update.message.reply_text(
                        "❌ Invalid user identifier. Use @username or numeric user ID."
                    )
                    return

            if not user:
                await update.message.reply_text(
                    f"❌ User `{user_identifier}` not found in system.", parse_mode="Markdown"
                )
                return

            # Get message count for current chat
            current_chat_id = update.effective_chat.id if update.effective_chat else 0
            message_count = await self.message_archiver.get_user_message_count(
                user_id=user.user_id, chat_id=current_chat_id
            )

            # Format user information
            user_info = "👤 **User Information**\n\n"
            user_info += f"**ID:** `{user.user_id}`\n"

            if user.username:
                user_info += f"**Username:** @{user.username}\n"

            if user.first_name:
                name_parts = [user.first_name]
                if user.last_name:
                    name_parts.append(user.last_name)
                user_info += f"**Name:** {' '.join(name_parts)}\n"

            user_info += f"**Bot:** {'Yes' if user.is_bot else 'No'}\n"
            user_info += f"**Admin:** {'Yes' if user.is_admin else 'No'}\n\n"

            # Activity information
            user_info += "**Activity in This Chat:**\n"
            user_info += f"• Messages: {message_count}\n"

            if user.last_message_at:
                time_diff = datetime.utcnow() - user.last_message_at
                if time_diff.days > 0:
                    user_info += f"• Last message: {time_diff.days} days ago\n"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    user_info += f"• Last message: {hours} hours ago\n"
                else:
                    minutes = time_diff.seconds // 60
                    user_info += f"• Last message: {minutes} minutes ago\n"
            else:
                user_info += "• Last message: Never\n"

            if user.join_date:
                join_diff = datetime.utcnow() - user.join_date
                user_info += f"• Member since: {join_diff.days} days ago\n"

            await update.message.reply_text(user_info, parse_mode="Markdown")

            logger.info(
                "User lookup completed",
                lookup_user=user_identifier,
                found_user_id=user.user_id,
                chat_id=current_chat_id,
            )

        except Exception as e:
            logger.error("Failed to lookup user", user_identifier=user_identifier, error=str(e))
            await update.message.reply_text("❌ Error looking up user information.")

    async def get_user_by_username(self, username: str) -> None:
        """Get user by username (placeholder method)."""
        # This would be implemented in the actual UserTracker
        # For now, return None to trigger user not found
        return None
