"""Telegram Bot Core - Phase 3 implementation."""

import os
import random
import re
import string
from datetime import datetime, timedelta
from typing import Any

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes

from ..config.loader import ConfigLoader
from ..config.schemas import ChannelEntry, ChannelsConfig, GlobalConfig, PuzzlesConfig

logger = structlog.get_logger(__name__)


class TelegramBot:
    """Main Telegram bot class for anti-lurk functionality."""

    def __init__(self) -> None:
        """Initialize the bot with environment validation."""
        # Validate required environment variables
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_TOKEN environment variable is required")
        self.token: str = token

        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Initialize configuration
        config_dir = os.environ.get("CONFIG_DIR")
        if config_dir:
            from pathlib import Path

            self.config_loader = ConfigLoader(config_dir=Path(config_dir))
        else:
            self.config_loader = ConfigLoader()

        # Load configurations
        self.global_config: GlobalConfig
        self.channels_config: ChannelsConfig
        self.puzzles_config: PuzzlesConfig
        self.global_config, self.channels_config, self.puzzles_config = (
            self.config_loader.load_all()
        )

        # Active link tracking for handshake
        self._active_links: dict[str, dict[str, Any]] = {}

        logger.info("TelegramBot initialized", token_prefix=self.token[:8])

    async def post_startup_message(self) -> None:
        """Post 'bot is live' message to all modlog channels."""
        modlog_channels = self.channels_config.get_modlog_channels()

        # Create application just for sending messages
        app = Application.builder().token(self.token).build()

        for channel in modlog_channels:
            try:
                await app.bot.send_message(
                    chat_id=channel.chat_id,
                    text="🤖 Telegram Anti-Lurk Bot is now online and monitoring.",
                )
                logger.info(
                    "Posted startup message", chat_id=channel.chat_id, chat_name=channel.chat_name
                )
            except Exception as e:
                logger.error(
                    "Failed to post startup message", chat_id=channel.chat_id, error=str(e)
                )

    async def handle_mode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /antlurk mode command."""
        if not update.message or not update.effective_chat:
            return

        if not context.args:
            # No arguments - show mode selection buttons
            await self._send_mode_selection_buttons(update, context)
            return

        mode = context.args[0].lower()
        if mode not in ["moderated", "modlog"]:
            await update.message.reply_text("❌ Invalid mode. Use 'moderated' or 'modlog'.")
            return

        # Set the chat mode
        chat_id = update.effective_chat.id
        chat_name = update.effective_chat.title or f"Chat {chat_id}"
        await self._set_chat_mode(chat_id, chat_name, mode, update)

    async def _send_mode_selection_buttons(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Send inline keyboard buttons for mode selection."""
        if not update.message:
            return

        keyboard = [
            [
                InlineKeyboardButton("📝 Moderated", callback_data="mode_moderated"),
                InlineKeyboardButton("📊 Modlog", callback_data="mode_modlog"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🛠️ Select the operating mode for this chat:\n\n"
            "• **Moderated**: Monitor user activity and send challenges\n"
            "• **Modlog**: Receive admin notifications and reports",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _set_chat_mode(self, chat_id: int, chat_name: str, mode: str, update: Update) -> None:
        """Set chat mode and update configuration."""
        # Find existing channel or create new one
        existing_channel = None
        for channel in self.channels_config.channels:
            if channel.chat_id == chat_id:
                existing_channel = channel
                break

        if existing_channel:
            # Update existing channel
            existing_channel.mode = mode
            existing_channel.chat_name = chat_name
        else:
            # Create new channel entry
            new_channel = ChannelEntry(chat_id=chat_id, chat_name=chat_name, mode=mode)
            self.channels_config.channels.append(new_channel)

        # Save configuration
        self.config_loader.save_channels_config(self.channels_config)

        # Send confirmation
        if update.message:
            emoji = "📝" if mode == "moderated" else "📊"
            await update.message.reply_text(
                f"{emoji} Chat mode set to **{mode}**.\n\n"
                f"This chat will now operate as a {mode} channel.",
                parse_mode="Markdown",
            )

        logger.info("Chat mode updated", chat_id=chat_id, chat_name=chat_name, mode=mode)

    async def handle_link_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate link code for moderated chat to connect with modlog."""
        if not update.effective_chat or not update.message:
            return

        chat_id = update.effective_chat.id
        chat_name = update.effective_chat.title or f"Chat {chat_id}"

        # Generate unique link code
        link_code = self._generate_link_code()

        # Store active link with 10-minute expiry
        self._active_links[link_code] = {
            "chat_id": chat_id,
            "chat_name": chat_name,
            "expires_at": datetime.utcnow() + timedelta(minutes=10),
            "message_id": None,  # Will be set after sending
        }

        # Send link message
        link_text = (
            f"🔗 **Link Code: {link_code}**\n\n"
            f"Forward this message to your modlog channel to establish the connection.\n\n"
            f"⏰ This link expires in 10 minutes."
        )

        message = await update.message.reply_text(link_text, parse_mode="Markdown")

        # Store message ID for potential deletion
        self._active_links[link_code]["message_id"] = message.message_id

        logger.info(
            "Link code generated",
            chat_id=chat_id,
            link_code=link_code,
            expires_at=self._active_links[link_code]["expires_at"],
        )

    async def handle_forwarded_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Process forwarded link messages in modlog chats."""
        if not update.message or not update.effective_chat:
            return

        if not update.message.forward_origin:
            return  # Not a forwarded message

        message_text = update.message.text or ""
        link_code = self._extract_link_code(message_text)

        if not link_code or not self._is_link_valid(link_code):
            return  # Not a valid link message

        modlog_chat_id = update.effective_chat.id
        modlog_chat_name = update.effective_chat.title or f"Chat {modlog_chat_id}"

        # Get original chat info
        link_info = self._active_links[link_code]
        moderated_chat_id = link_info["chat_id"]
        moderated_chat_name = link_info["chat_name"]

        # Create the channel link
        await self._create_channel_link(
            moderated_chat_id=moderated_chat_id,
            moderated_chat_name=moderated_chat_name,
            modlog_chat_id=modlog_chat_id,
            modlog_chat_name=modlog_chat_name,
            link_code=link_code,
        )

    async def _create_channel_link(
        self,
        moderated_chat_id: int,
        moderated_chat_name: str,
        modlog_chat_id: int,
        modlog_chat_name: str,
        link_code: str,
    ) -> None:
        """Create bidirectional link between moderated and modlog chats."""
        # Update channels configuration
        moderated_found = False
        modlog_found = False

        for channel in self.channels_config.channels:
            if channel.chat_id == moderated_chat_id:
                channel.modlog_ref = modlog_chat_id
                moderated_found = True
            elif channel.chat_id == modlog_chat_id:
                modlog_found = True

        # Add channels if they don't exist
        if not moderated_found:
            moderated_channel = ChannelEntry(
                chat_id=moderated_chat_id,
                chat_name=moderated_chat_name,
                mode="moderated",
                modlog_ref=modlog_chat_id,
            )
            self.channels_config.channels.append(moderated_channel)

        if not modlog_found:
            modlog_channel = ChannelEntry(
                chat_id=modlog_chat_id, chat_name=modlog_chat_name, mode="modlog"
            )
            self.channels_config.channels.append(modlog_channel)

        # Save configuration
        self.config_loader.save_channels_config(self.channels_config)

        # Clean up the link
        del self._active_links[link_code]

        logger.info(
            "Channel link established",
            moderated_chat_id=moderated_chat_id,
            moderated_chat_name=moderated_chat_name,
            modlog_chat_id=modlog_chat_id,
            modlog_chat_name=modlog_chat_name,
            link_code=link_code,
        )

    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /antlurk help command."""
        if not update.message:
            return

        help_text = (
            "🤖 **Telegram Anti-Lurk Bot Help**\n\n"
            "**Available Commands:**\n"
            "• `/antlurk help` - Show this help message\n"
            "• `/antlurk mode` - Set chat operating mode\n"
            "• `/antlurk mode moderated` - Set as moderated chat\n"
            "• `/antlurk mode modlog` - Set as modlog chat\n\n"
            "**Chat Types:**\n"
            "• **Moderated**: Chats where user activity is monitored and challenges are sent\n"
            "• **Modlog**: Chats that receive admin notifications and reports\n\n"
            "**Setup Process:**\n"
            "1. Set one chat as 'moderated' where users will be monitored\n"
            "2. Set another chat as 'modlog' to receive admin notifications\n"
            "3. Link them together using the forward-code handshake\n\n"
            "Need more help? Check the documentation or contact your administrator."
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    def _generate_link_code(self) -> str:
        """Generate a unique 6-character alphanumeric link code."""
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self._active_links:
                return code

    def _extract_link_code(self, message_text: str) -> str | None:
        """Extract link code from forwarded message text."""
        # Look for pattern: "Link Code: ABC123"
        match = re.search(r"Link Code: ([A-Z0-9]{6})", message_text)
        return match.group(1) if match else None

    def _is_link_valid(self, link_code: str) -> bool:
        """Check if a link code is valid and not expired."""
        if link_code not in self._active_links:
            return False

        link_info = self._active_links[link_code]
        expires_at = link_info["expires_at"]
        return bool(datetime.utcnow() < expires_at)
