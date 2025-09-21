"""Report command handler for generating user activity reports."""

from datetime import datetime, timedelta

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from ..audit.lurker_selector import LurkerSelector
from ..config.loader import ConfigLoader
from ..logging.user_tracker import UserTracker

logger = structlog.get_logger(__name__)


class ReportCommandHandler:
    """Handles /antlurk report commands for activity reports."""

    def __init__(
        self,
        config_loader: ConfigLoader | None = None,
        user_tracker: UserTracker | None = None,
        lurker_selector: LurkerSelector | None = None,
    ) -> None:
        """Initialize report command handler."""
        self.config_loader = config_loader or ConfigLoader()
        self.user_tracker = user_tracker or UserTracker()
        self.lurker_selector = lurker_selector

    async def handle_report_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /antlurk report active|inactive|lurkers [--days N] [--limit M] command."""
        if not update.message or not update.effective_chat or not context.args:
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: `/antlurk report active|inactive|lurkers [--days N] [--limit M]`\n\n"
                    "Examples:\n"
                    "• `/antlurk report active --limit 10`\n"
                    "• `/antlurk report lurkers --days 7 --limit 5`\n"
                    "• `/antlurk report inactive --days 30`",
                    parse_mode="Markdown",
                )
            return

        # Verify this is a moderated chat
        if not await self._is_moderated_chat(update.effective_chat.id):
            await update.message.reply_text("❌ Reports can only be generated in moderated chats.")
            return

        # Parse arguments
        report_type = context.args[0].lower()
        days = self._parse_arg_value(context.args, "--days", 14)  # default 14 days
        limit = self._parse_arg_value(context.args, "--limit", 20)  # default 20 users

        # Clamp values
        days = max(1, min(days, 365))
        limit = max(1, min(limit, 100))

        try:
            if report_type == "active":
                await self._generate_active_report(update, days, limit)
            elif report_type == "inactive":
                await self._generate_inactive_report(update, days, limit)
            elif report_type == "lurkers":
                await self._generate_lurkers_report(update, days, limit)
            else:
                await update.message.reply_text(
                    "❌ Invalid report type. Use: `active`, `inactive`, or `lurkers`",
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error("Failed to generate report", report_type=report_type, error=str(e))
            await update.message.reply_text("❌ Error generating report.")

    async def _generate_active_report(self, update: Update, days: int, limit: int) -> None:
        """Generate report of active users."""
        if not update.message or not update.effective_chat:
            return

        since_date = datetime.utcnow() - timedelta(days=days)
        active_users = await self.user_tracker.get_users_by_activity(
            chat_id=update.effective_chat.id, since=since_date
        )

        # Sort by last message time (most recent first)
        active_users.sort(key=lambda u: u.last_message_at or datetime.min, reverse=True)
        active_users = active_users[:limit]

        report_text = "📊 **Active Users Report**\n\n"
        report_text += f"Users active in the last {days} days (showing {len(active_users)}):\n\n"

        if not active_users:
            report_text += "No active users found in the specified period."
        else:
            for i, user in enumerate(active_users, 1):
                username = f"@{user.username}" if user.username else f"ID:{user.user_id}"
                if user.last_message_at:
                    time_diff = datetime.utcnow() - user.last_message_at
                    if time_diff.days > 0:
                        last_seen = f"{time_diff.days}d ago"
                    elif time_diff.seconds > 3600:
                        last_seen = f"{time_diff.seconds // 3600}h ago"
                    else:
                        last_seen = f"{time_diff.seconds // 60}m ago"
                else:
                    last_seen = "Never"

                report_text += f"{i}. {username} - Last: {last_seen}\n"

        await update.message.reply_text(report_text, parse_mode="Markdown")

    async def _generate_inactive_report(self, update: Update, days: int, limit: int) -> None:
        """Generate report of inactive users."""
        if not update.message or not update.effective_chat:
            return

        inactive_since = datetime.utcnow() - timedelta(days=days)
        inactive_users = await self.user_tracker.get_inactive_users(
            chat_id=update.effective_chat.id, inactive_since=inactive_since
        )

        # Sort by last message time (least recent first)
        inactive_users.sort(key=lambda u: u.last_message_at or datetime.min)
        inactive_users = inactive_users[:limit]

        report_text = "📊 **Inactive Users Report**\n\n"
        report_text += (
            f"Users inactive for more than {days} days (showing {len(inactive_users)}):\n\n"
        )

        if not inactive_users:
            report_text += "No inactive users found matching the criteria."
        else:
            for i, user in enumerate(inactive_users, 1):
                username = f"@{user.username}" if user.username else f"ID:{user.user_id}"
                if user.last_message_at:
                    time_diff = datetime.utcnow() - user.last_message_at
                    inactive_for = f"{time_diff.days}d"
                else:
                    inactive_for = "Never active"

                report_text += f"{i}. {username} - Inactive: {inactive_for}\n"

        await update.message.reply_text(report_text, parse_mode="Markdown")

    async def _generate_lurkers_report(self, update: Update, days: int, limit: int) -> None:
        """Generate report of lurkers (users eligible for challenges)."""
        if not update.message or not update.effective_chat:
            return

        # Use injected lurker selector or create one
        if self.lurker_selector:
            lurker_selector = self.lurker_selector
        else:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            lurker_selector = LurkerSelector(global_config)

        lurkers = await lurker_selector.get_lurkers_for_chat(
            chat_id=update.effective_chat.id, days_threshold=days
        )

        lurkers = lurkers[:limit]

        report_text = "🎯 **Lurkers Report**\n\n"
        report_text += (
            f"Users eligible for challenges ({days}+ days inactive, showing {len(lurkers)}):\n\n"
        )

        if not lurkers:
            report_text += "No lurkers found matching the criteria."
        else:
            for i, user in enumerate(lurkers, 1):
                username = f"@{user.username}" if user.username else f"ID:{user.user_id}"
                if user.last_message_at:
                    time_diff = datetime.utcnow() - user.last_message_at
                    inactive_for = f"{time_diff.days}d"
                else:
                    inactive_for = "Never active"

                report_text += f"{i}. {username} - Inactive: {inactive_for}\n"

        await update.message.reply_text(report_text, parse_mode="Markdown")

    def _parse_arg_value(self, args: list[str], flag: str, default: int) -> int:
        """Parse a --flag value from command arguments."""
        try:
            flag_index = args.index(flag)
            if flag_index + 1 < len(args):
                return int(args[flag_index + 1])
        except (ValueError, IndexError):
            pass
        return default

    async def _is_moderated_chat(self, chat_id: int) -> bool:
        """Check if chat is configured as moderated."""
        try:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            moderated_channels = channels_config.get_moderated_channels()
            return any(channel.chat_id == chat_id for channel in moderated_channels)
        except Exception:
            return False
