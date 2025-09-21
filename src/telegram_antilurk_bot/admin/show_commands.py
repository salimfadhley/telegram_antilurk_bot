"""Show command handlers for displaying system state."""

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from ..config.loader import ConfigLoader
from ..logging.provocation_logger import ProvocationLogger

logger = structlog.get_logger(__name__)


class ShowCommandHandler:
    """Handles /antlurk show commands for displaying system information."""

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """Initialize show command handler."""
        self.config_loader = config_loader or ConfigLoader()
        self.provocation_logger = ProvocationLogger()

    async def handle_show_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /antlurk show subcommands."""
        if not update.message or not context.args:
            if update.message:
                await update.message.reply_text(
                    "❌ Usage: `/antlurk show links|config|reports [limit]`", parse_mode="Markdown"
                )
            return

        subcommand = context.args[0].lower()

        if subcommand == "links":
            await self._show_links(update, context)
        elif subcommand == "config":
            await self._show_config(update, context)
        elif subcommand == "reports":
            await self._show_reports(update, context)
        else:
            await update.message.reply_text(
                "❌ Invalid subcommand. Use: `links`, `config`, or `reports`", parse_mode="Markdown"
            )

    async def _show_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display current chat linkages."""
        if not update.message:
            return

        try:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()

            links_text = "🔗 **Chat Linkages**\n\n"

            moderated_channels = channels_config.get_moderated_channels()
            if not moderated_channels:
                links_text += "No moderated chats configured.\n"
            else:
                for moderated in moderated_channels:
                    links_text += f"📝 **{moderated.chat_name}** (`{moderated.chat_id}`)\n"

                    if moderated.modlog_ref:
                        # Find the linked modlog
                        modlog = next(
                            (
                                ch
                                for ch in channels_config.channels
                                if ch.chat_id == moderated.modlog_ref
                            ),
                            None,
                        )
                        if modlog:
                            links_text += f"   └── 📊 {modlog.chat_name} (`{modlog.chat_id}`)\n"
                        else:
                            links_text += (
                                f"   └── ⚠️ Linked to unknown chat (`{moderated.modlog_ref}`)\n"
                            )
                    else:
                        links_text += "   └── ❌ No modlog linked\n"
                    links_text += "\n"

            # Show standalone modlog channels
            modlog_channels = channels_config.get_modlog_channels()
            standalone_modlogs = [
                modlog
                for modlog in modlog_channels
                if not any(mod.modlog_ref == modlog.chat_id for mod in moderated_channels)
            ]

            if standalone_modlogs:
                links_text += "📊 **Standalone Modlog Chats**\n"
                for modlog in standalone_modlogs:
                    links_text += f"• {modlog.chat_name} (`{modlog.chat_id}`)\n"

            await update.message.reply_text(links_text, parse_mode="Markdown")

        except Exception as e:
            logger.error("Failed to show links", error=str(e))
            await update.message.reply_text("❌ Error retrieving chat linkages.")

    async def _show_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display current effective configuration."""
        if not update.message:
            return

        try:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()

            config_text = "⚙️ **Current Configuration**\n\n"

            config_text += "**Global Settings:**\n"
            config_text += f"• Lurk threshold: {global_config.lurk_threshold_days} days\n"
            config_text += (
                f"• Provocation interval: {global_config.provocation_interval_hours} hours\n"
            )
            config_text += f"• Audit cadence: {global_config.audit_cadence_minutes} minutes\n"
            config_text += f"• Rate limit: {global_config.rate_limit_per_hour}/hour, {global_config.rate_limit_per_day}/day\n"
            config_text += f"• NATS enabled: {global_config.enable_nats}\n"
            config_text += f"• Announcements: {global_config.enable_announcements}\n\n"

            config_text += "**Statistics:**\n"
            config_text += f"• Configured chats: {len(channels_config.channels)}\n"
            config_text += f"• Available puzzles: {len(puzzles_config.puzzles)}\n"

            # Show last updated info
            config_text += "\n**Last Updated:**\n"
            config_text += (
                f"• Config: {global_config.provenance.updated_at.strftime('%Y-%m-%d %H:%M')} UTC\n"
            )
            config_text += f"• By: {global_config.provenance.updated_by}\n"

            await update.message.reply_text(config_text, parse_mode="Markdown")

        except Exception as e:
            logger.error("Failed to show config", error=str(e))
            await update.message.reply_text("❌ Error retrieving configuration.")

    async def _show_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display recent moderation reports (moderated chats only)."""
        if not update.message or not update.effective_chat:
            return

        try:
            # Verify this is a moderated chat
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            moderated_channels = channels_config.get_moderated_channels()

            current_chat_id = update.effective_chat.id
            is_moderated = any(ch.chat_id == current_chat_id for ch in moderated_channels)

            if not is_moderated:
                await update.message.reply_text("❌ Reports can only be viewed in moderated chats.")
                return

            # Parse limit argument
            limit = 10  # default
            if context.args and len(context.args) > 1:
                try:
                    limit = int(context.args[1])
                    limit = max(1, min(limit, 50))  # clamp between 1-50
                except ValueError:
                    pass

            # Get recent reports
            recent_reports = await self.provocation_logger.get_recent_provocations(
                chat_id=current_chat_id, limit=limit
            )

            if not recent_reports:
                await update.message.reply_text(
                    "📊 **Recent Reports**\n\nNo recent moderation activity in this chat."
                )
                return

            reports_text = f"📊 **Recent Reports** (last {len(recent_reports)})\n\n"

            for report in recent_reports:
                timestamp = report["timestamp"].strftime("%m-%d %H:%M")
                event_icon = {
                    "created": "🎯",
                    "response": "✅" if report.get("is_correct") else "❌",
                    "failed": "❌",
                    "expired": "⏰",
                    "completed": "✅",
                }.get(report["event"], "📝")

                reports_text += f"{event_icon} `{timestamp}` "
                reports_text += f"User {report.get('user_id', 'Unknown')} "
                reports_text += f"- {report['event'].title()}"

                if "provocation_id" in report:
                    reports_text += f" (#{report['provocation_id']})"

                reports_text += "\n"

            await update.message.reply_text(reports_text, parse_mode="Markdown")

        except Exception as e:
            logger.error("Failed to show reports", error=str(e))
            await update.message.reply_text("❌ Error retrieving reports.")
