"""Core bot application orchestration."""

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..admin.checkuser_command import CheckUserCommandHandler
from ..admin.reboot_command import RebootCommandHandler
from ..admin.show_commands import ShowCommandHandler
from ..admin.unlink_command import UnlinkCommandHandler
from ..admin.report_command import ReportCommandHandler
from ..bot.core import TelegramBot
from ..config.loader import ConfigLoader

logger = structlog.get_logger(__name__)


class BotApplication:
    """Main bot application orchestrator."""

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """Initialize bot application."""
        self.config_loader = config_loader or ConfigLoader()
        self.telegram_bot = TelegramBot()
        # Admin/command handlers
        self._show = ShowCommandHandler(self.config_loader)
        self._report = ReportCommandHandler(self.config_loader)
        self._unlink = UnlinkCommandHandler(self.config_loader)
        self._reboot = RebootCommandHandler(self.config_loader)
        self._check = CheckUserCommandHandler()
        logger.info("Bot application initialized")

    async def register_handlers(self, app: Application) -> None:
        """Register all bot handlers with the Telegram application."""
        # Primary command dispatcher: /antlurk [subcommand]
        app.add_handler(CommandHandler("antlurk", self._dispatch_antlurk))

        # Onboarding shortcut: /start shows the same mode selection welcome
        app.add_handler(CommandHandler("start", self._start_command))

        # Forwarded code handler to link moderated ↔ modlog chats
        app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, self.telegram_bot.handle_forwarded_message))

        # Mode selection via inline buttons
        app.add_handler(CallbackQueryHandler(self._on_mode_callback, pattern=r"^mode_(moderated|modlog)$"))

        # Welcome/onboarding when the bot is added to a chat
        app.add_handler(ChatMemberHandler(self._on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

        logger.info("Bot handlers registered")

    async def persist_state(self) -> None:
        """Persist any in-memory application state."""
        logger.info("Application state persisted")

    # --- Internal handlers/dispatchers ---
    async def _dispatch_antlurk(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Dispatch /antlurk subcommands to their handlers."""
        args = context.args or []
        if not args:
            # No args: present mode selection as a welcome
            await self.telegram_bot._send_mode_selection_buttons(update, context)
            return

        sub = args[0].lower()
        # Route to specific handlers
        if sub == "help":
            await self.telegram_bot.handle_help_command(update, context)
        elif sub == "mode":
            await self.telegram_bot.handle_mode_command(update, context)
        elif sub == "link":
            await self.telegram_bot.handle_link_request(update, context)
        elif sub == "show":
            await self._show.handle_show_command(update, context)
        elif sub == "report":
            await self._report.handle_report_command(update, context)
        elif sub == "unlink":
            await self._unlink.handle_unlink_command(update, context)
        elif sub == "reboot":
            await self._reboot.handle_reboot_command(update, context)
        elif sub == "checkuser":
            await self._check.handle_checkuser_command(update, context)
        else:
            # Unknown: show help summary
            await self.telegram_bot.handle_help_command(update, context)

    async def _on_mode_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline button mode selection callbacks."""
        if not update.callback_query:
            return
        query = update.callback_query
        data = (query.data or "").strip().lower()
        mode = "moderated" if data.endswith("moderated") else "modlog"
        chat = update.effective_chat
        if not chat:
            await query.answer()
            return
        await self.telegram_bot._set_chat_mode(chat.id, chat.title or f"Chat {chat.id}", mode, update)
        await query.answer(text=f"Mode set to {mode}")

    async def _on_my_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a welcome with mode selection when the bot is added to a chat."""
        if not update.my_chat_member or not update.effective_chat:
            return
        chat_id = update.effective_chat.id
        # Compose inline keyboard for mode selection
        keyboard = [[
            InlineKeyboardButton("📝 Moderated", callback_data="mode_moderated"),
            InlineKeyboardButton("📊 Modlog", callback_data="mode_modlog"),
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "👋 Thanks for adding me!\n\n"
                    "Please choose how this chat should operate:\n\n"
                    "• 📝 Moderated — monitor users and send challenges\n"
                    "• 📊 Modlog — receive admin notifications and reports"
                ),
                reply_markup=reply_markup,
            )
            logger.info("Welcome message sent", chat_id=chat_id)
        except Exception as e:
            logger.error("Failed to send welcome message", chat_id=chat_id, error=str(e))

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start by presenting the mode selection welcome message."""
        # Reuse the same UI we show on onboarding and `/antlurk` with no args
        await self.telegram_bot._send_mode_selection_buttons(update, context)
