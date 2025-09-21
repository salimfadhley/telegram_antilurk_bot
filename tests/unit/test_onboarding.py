"""Unit tests for onboarding and /start behavior."""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.asyncio
async def test_welcome_message_sent_on_bot_added(temp_config_dir):
    """When the bot is added to a chat, it should send a welcome with mode buttons."""
    from telegram_antilurk_bot.core.bot import BotApplication

    # Minimal update/context mocks
    mock_update = Mock()
    mock_update.my_chat_member = Mock()  # Presence triggers handler
    mock_update.effective_chat = Mock()
    mock_update.effective_chat.id = -1002223334445
    mock_update.effective_chat.title = "Welcome Chat"

    mock_context = Mock()
    mock_context.bot = Mock()
    mock_context.bot.send_message = AsyncMock()

    with patch.dict(
        "os.environ",
        {
            "TELEGRAM_TOKEN": "test_token",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CONFIG_DIR": str(temp_config_dir),
        },
    ):
        app = BotApplication()
        await app._on_my_chat_member(mock_update, mock_context)

        # Should send exactly one welcome message
        mock_context.bot.send_message.assert_called_once()
        args, kwargs = mock_context.bot.send_message.call_args
        # Validate destination and content
        assert kwargs["chat_id"] == -1002223334445
        assert "Thanks for adding me" in kwargs["text"]
        # Inline keyboard with mode buttons should be present
        reply_markup = kwargs.get("reply_markup")
        assert reply_markup is not None
        # InlineKeyboardMarkup exposes "inline_keyboard" attribute (list of rows)
        inline = getattr(reply_markup, "inline_keyboard", [])
        # Expect two buttons in the first row with our callback_data
        assert len(inline) >= 1 and len(inline[0]) >= 2
        datas = {getattr(btn, "callback_data", None) for btn in inline[0]}
        assert "mode_moderated" in datas and "mode_modlog" in datas


@pytest.mark.asyncio
async def test_start_command_reuses_mode_selection_ui(temp_config_dir):
    """/start should reuse the same mode selection UI as other commands (single root)."""
    from telegram_antilurk_bot.core.bot import BotApplication

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
        app = BotApplication()
        # Patch the underlying TelegramBot method to ensure consistency
        with patch.object(app.telegram_bot, "_send_mode_selection_buttons", new=AsyncMock()) as mock_send:
            await app._start_command(mock_update, mock_context)
            mock_send.assert_called_once_with(mock_update, mock_context)

