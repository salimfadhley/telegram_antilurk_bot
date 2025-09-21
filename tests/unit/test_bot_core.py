"""Unit tests for Telegram Bot Core - TDD approach for Phase 3."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestBotStartup:
    """Tests for bot initialization and startup validation."""

    def test_bot_validates_required_environment_variables(self) -> None:
        """Bot should validate TELEGRAM_TOKEN and DATABASE_URL on startup."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        # Missing TELEGRAM_TOKEN should raise error
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
                TelegramBot()

        # Missing DATABASE_URL should raise error
        with patch.dict("os.environ", {"TELEGRAM_TOKEN": "test_token"}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL"):
                TelegramBot()

    def test_bot_initializes_with_valid_environment(self, temp_config_dir: Path) -> None:
        """Bot should initialize successfully with valid environment."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token_123456789:ABCdefGhIJKlmNoPQRstuVwxyZ",
                "DATABASE_URL": "postgresql://test:test@localhost:5432/test_antilurk",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()
            assert bot.token == "test_token_123456789:ABCdefGhIJKlmNoPQRstuVwxyZ"
            assert bot.config_loader is not None

    @pytest.mark.asyncio
    async def test_bot_posts_startup_message_to_modlogs(self, temp_config_dir: Path) -> None:
        """Bot should post 'bot is live' message to all modlog channels on startup."""
        from telegram_antilurk_bot.bot.core import TelegramBot
        from telegram_antilurk_bot.config.schemas import ChannelEntry, ChannelsConfig

        # Create mock channels config with modlog channels
        modlog_channels = [
            ChannelEntry(chat_id=-1001234567890, chat_name="Test Modlog 1", mode="modlog"),
            ChannelEntry(chat_id=-1009876543210, chat_name="Test Modlog 2", mode="modlog"),
        ]

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            with patch("telegram_antilurk_bot.bot.core.Application") as mock_app:
                mock_bot = AsyncMock()
                mock_app.builder().token().build.return_value.bot = mock_bot

                bot = TelegramBot()

                # Mock the config to return modlog channels
                bot.channels_config = ChannelsConfig(channels=modlog_channels)

                await bot.post_startup_message()

                # Should send message to both modlog channels
                assert mock_bot.send_message.call_count == 2
                mock_bot.send_message.assert_any_call(
                    chat_id=-1001234567890,
                    text="🤖 Telegram Anti-Lurk Bot is now online and monitoring.",
                )
                mock_bot.send_message.assert_any_call(
                    chat_id=-1009876543210,
                    text="🤖 Telegram Anti-Lurk Bot is now online and monitoring.",
                )


class TestModeCommands:
    """Tests for /antlurk mode command functionality."""

    @pytest.mark.asyncio
    async def test_mode_command_shows_buttons_when_no_args(self, temp_config_dir: Path) -> None:
        """'/antlurk mode' should show inline buttons for mode selection."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_context = Mock()
        mock_context.args = None  # No arguments

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            with patch.object(bot, "_send_mode_selection_buttons") as mock_send:
                await bot.handle_mode_command(mock_update, mock_context)
                mock_send.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_mode_command_sets_moderated_mode(self, temp_config_dir: Path) -> None:
        """'/antlurk mode moderated' should set chat to moderated mode."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.effective_chat.title = "Test Channel"
        mock_context = Mock()
        mock_context.args = ["moderated"]

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            with patch.object(bot, "_set_chat_mode") as mock_set_mode:
                await bot.handle_mode_command(mock_update, mock_context)
                mock_set_mode.assert_called_once_with(
                    -1001234567890, "Test Channel", "moderated", mock_update
                )

    @pytest.mark.asyncio
    async def test_mode_command_sets_modlog_mode(self, temp_config_dir: Path) -> None:
        """'/antlurk mode modlog' should set chat to modlog mode."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_update.effective_chat.id = -1009876543210
        mock_update.effective_chat.title = "Test Modlog"
        mock_context = Mock()
        mock_context.args = ["modlog"]

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            with patch.object(bot, "_set_chat_mode") as mock_set_mode:
                await bot.handle_mode_command(mock_update, mock_context)
                mock_set_mode.assert_called_once_with(
                    -1009876543210, "Test Modlog", "modlog", mock_update
                )

    @pytest.mark.asyncio
    async def test_mode_command_rejects_invalid_mode(self, temp_config_dir: Path) -> None:
        """'/antlurk mode invalid' should show error message."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_context = Mock()
        mock_context.args = ["invalid"]

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            with patch.object(mock_update, "message") as mock_message:
                mock_message.reply_text = AsyncMock()
                await bot.handle_mode_command(mock_update, mock_context)
                mock_message.reply_text.assert_called_once_with(
                    "❌ Invalid mode. Use 'moderated' or 'modlog'."
                )


class TestLinkingHandshake:
    """Tests for forward-code handshake linking functionality."""

    @pytest.mark.asyncio
    async def test_generates_link_message_in_moderated_chat(self, temp_config_dir: Path) -> None:
        """Bot should generate forward-code link message in moderated chat."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.effective_chat.title = "Test Moderated"
        mock_context = Mock()

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            with patch.object(bot, "_generate_link_code", return_value="ABC123"):
                with patch.object(mock_update, "message") as mock_message:
                    # Mock the reply_text to return a coroutine with message_id
                    mock_reply = Mock()
                    mock_reply.message_id = 12345
                    mock_message.reply_text = AsyncMock(return_value=mock_reply)

                    await bot.handle_link_request(mock_update, mock_context)

                    # Should send link message with code
                    mock_message.reply_text.assert_called_once()
                    call_args = mock_message.reply_text.call_args[0]
                    assert "ABC123" in call_args[0]
                    assert "forward this message" in call_args[0].lower()

    @pytest.mark.asyncio
    async def test_link_message_expires_after_10_minutes(self, temp_config_dir: Path) -> None:
        """Link message should have 10-minute TTL and auto-delete."""
        from datetime import datetime, timedelta

        from telegram_antilurk_bot.bot.core import TelegramBot

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            # Create mock link entry
            link_code = "ABC123"
            chat_id = -1001234567890

            bot._active_links[link_code] = {
                "chat_id": chat_id,
                "chat_name": "Test Channel",
                "expires_at": datetime.utcnow() + timedelta(minutes=10),
                "message_id": 12345,
            }

            # Test that fresh link is valid
            assert bot._is_link_valid(link_code) is True

            # Test that expired link is invalid
            bot._active_links[link_code]["expires_at"] = datetime.utcnow() - timedelta(minutes=1)
            assert bot._is_link_valid(link_code) is False

    @pytest.mark.asyncio
    async def test_processes_forwarded_link_in_modlog(self, temp_config_dir: Path) -> None:
        """Bot should process forwarded link message in modlog chat."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_update.effective_chat.id = -1009876543210  # modlog chat
        mock_update.effective_chat.title = "Test Modlog"
        mock_update.message.forward_origin = Mock()  # indicates forwarded message
        mock_update.message.text = "🔗 Link Code: ABC123"

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            # Setup active link
            bot._active_links["ABC123"] = {
                "chat_id": -1001234567890,
                "chat_name": "Test Moderated",
                "expires_at": datetime.utcnow() + timedelta(minutes=5),
                "message_id": 12345,
            }

            with patch.object(bot, "_create_channel_link") as mock_create_link:
                await bot.handle_forwarded_message(mock_update, Mock())

                mock_create_link.assert_called_once_with(
                    moderated_chat_id=-1001234567890,
                    moderated_chat_name="Test Moderated",
                    modlog_chat_id=-1009876543210,
                    modlog_chat_name="Test Modlog",
                    link_code="ABC123",
                )


class TestHelpCommand:
    """Tests for /antlurk help command."""

    @pytest.mark.asyncio
    async def test_help_command_lists_available_commands(self, temp_config_dir: Path) -> None:
        """'/antlurk help' should list all available commands and their usage."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_context = Mock()

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            with patch.object(mock_update, "message") as mock_message:
                mock_message.reply_text = AsyncMock()
                await bot.handle_help_command(mock_update, mock_context)

                mock_message.reply_text.assert_called_once()
                help_text = mock_message.reply_text.call_args[0][0]

                # Should contain key commands
                assert "/antlurk mode" in help_text
                assert "/antlurk help" in help_text
                assert "moderated" in help_text
                assert "modlog" in help_text

    @pytest.mark.asyncio
    async def test_help_command_explains_roles_and_permissions(self, temp_config_dir: Path) -> None:
        """Help command should explain where different commands can be used."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        mock_update = Mock()
        mock_context = Mock()

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            with patch.object(mock_update, "message") as mock_message:
                mock_message.reply_text = AsyncMock()
                await bot.handle_help_command(mock_update, mock_context)

                help_text = mock_message.reply_text.call_args[0][0]

                # Should explain chat types and permissions
                assert "moderated" in help_text.lower()
                assert "modlog" in help_text.lower()


class TestUtilityMethods:
    """Tests for internal utility methods."""

    def test_generate_link_code_creates_unique_codes(self, temp_config_dir: Path) -> None:
        """_generate_link_code should create unique alphanumeric codes."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            # Generate multiple codes
            codes = set()
            for _ in range(100):
                code = bot._generate_link_code()
                codes.add(code)
                assert len(code) == 6
                assert code.isalnum()
                # Code should be uppercase letters or digits (digits don't have case)
                assert all(c.isupper() or c.isdigit() for c in code)

            # Should have generated unique codes
            assert len(codes) == 100

    def test_extract_link_code_from_message(self, temp_config_dir: Path) -> None:
        """_extract_link_code should parse link code from forwarded messages."""
        from telegram_antilurk_bot.bot.core import TelegramBot

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "CONFIG_DIR": str(temp_config_dir),
            },
        ):
            bot = TelegramBot()

            # Test valid link message
            link_text = "🔗 Link Code: ABC123\n\nForward this message to your modlog channel..."
            code = bot._extract_link_code(link_text)
            assert code == "ABC123"

            # Test message without link code
            normal_text = "This is just a normal message"
            code = bot._extract_link_code(normal_text)
            assert code is None
