"""Unit tests for Challenge Flow - TDD approach for Phase 5."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import InlineKeyboardMarkup

from telegram_antilurk_bot.config.schemas import Puzzle
from telegram_antilurk_bot.database.models import User


class TestChallengeComposer:
    """Tests for composing and posting challenge messages."""

    @pytest.mark.asyncio
    async def test_composes_puzzle_message_with_randomized_choices(
        self, temp_config_dir: Path
    ) -> None:
        """Should compose puzzle with randomized choice order."""
        from telegram_antilurk_bot.challenges.composer import ChallengeComposer

        composer = ChallengeComposer()
        puzzle = Puzzle(
            id="test_puzzle_1",
            type="arithmetic",
            question="What is 2 + 2?",
            choices=["4", "3", "5"],  # First choice is correct
        )
        user = User(user_id=12345, username="testuser", first_name="Test")

        # Generate multiple messages to test randomization
        messages = []
        keyboards = []
        for _ in range(10):
            message_text, keyboard = composer.compose_challenge_message(puzzle, user)
            messages.append(message_text)
            keyboards.append(keyboard)

        # All messages should contain the question and mention the user
        for message in messages:
            assert "What is 2 + 2?" in message
            assert "@testuser" in message or "Test" in message

        # Keyboard choices should be randomized across multiple generations
        choice_orders = [
            tuple(btn.text for row in kb.inline_keyboard for btn in row) for kb in keyboards
        ]
        assert len(set(choice_orders)) > 1, "Choice order should be randomized"

    @pytest.mark.asyncio
    async def test_posts_challenge_to_moderated_chat(self, temp_config_dir: Path) -> None:
        """Should post challenge message to moderated chat."""
        from telegram_antilurk_bot.challenges.composer import ChallengeComposer

        composer = ChallengeComposer()
        puzzle = Puzzle(
            id="test_puzzle_2",
            type="common_sense",
            question="Which animal barks?",
            choices=["Dog", "Cat", "Bird"],  # First choice is correct
        )
        user = User(user_id=67890, username="lurker123")
        chat_id = -1001234567890

        with patch("telegram_antilurk_bot.challenges.composer.Application") as mock_app:
            mock_bot = AsyncMock()
            mock_app.builder().token().build.return_value.bot = mock_bot
            mock_message = Mock()
            mock_message.message_id = 12345
            mock_bot.send_message.return_value = mock_message

            message_id = await composer.post_challenge(chat_id, puzzle, user, "test_token")

            assert message_id == 12345
            mock_bot.send_message.assert_called_once()
            call_args = mock_bot.send_message.call_args
            assert call_args.kwargs["chat_id"] == chat_id
            assert "Which animal barks?" in call_args.kwargs["text"]
            assert isinstance(call_args.kwargs["reply_markup"], InlineKeyboardMarkup)


class TestProvocationTracker:
    """Tests for tracking challenge provocations in database."""

    @pytest.mark.asyncio
    async def test_creates_provocation_record(self, temp_config_dir: Path) -> None:
        """Should create provocation record in database."""
        from telegram_antilurk_bot.challenges.tracker import ProvocationTracker

        tracker = ProvocationTracker()
        puzzle_id = "test_puzzle_1"
        chat_id = -1001234567890
        user_id = 12345
        message_id = 67890

        provocation_id = await tracker.create_provocation(
            chat_id=chat_id,
            user_id=user_id,
            puzzle_id=puzzle_id,
            message_id=message_id,
            expiration_minutes=30,
        )

        assert isinstance(provocation_id, int)
        assert provocation_id > 0

        # Verify provocation was stored
        provocation = await tracker.get_provocation(provocation_id)
        assert provocation is not None
        assert provocation.chat_id == chat_id
        assert provocation.user_id == user_id
        assert provocation.puzzle_id == puzzle_id
        assert provocation.status == "pending"

    @pytest.mark.asyncio
    async def test_tracks_provocation_expiration(self, temp_config_dir: Path) -> None:
        """Should track when provocations expire."""
        from telegram_antilurk_bot.challenges.tracker import ProvocationTracker

        tracker = ProvocationTracker()

        # Create provocation with short expiration
        provocation_id = await tracker.create_provocation(
            chat_id=-1001234567890,
            user_id=12345,
            puzzle_id="test_puzzle_1",
            message_id=67890,
            expiration_minutes=1,  # 1 minute
        )

        # Initially should not be expired
        assert not await tracker.is_provocation_expired(provocation_id)

        # Mock time passage
        with patch("telegram_antilurk_bot.challenges.tracker.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(minutes=2)
            assert await tracker.is_provocation_expired(provocation_id)


class TestCallbackHandler:
    """Tests for handling inline keyboard button callbacks."""

    @pytest.mark.asyncio
    async def test_handles_correct_answer_callback(self, temp_config_dir: Path) -> None:
        """Should handle correct answer callback and update provocation status."""
        from telegram_antilurk_bot.challenges.callback_handler import CallbackHandler

        # Create mocked dependencies
        mock_tracker = AsyncMock()
        mock_notifier = AsyncMock()

        # Mock correct answer flow
        mock_tracker.validate_callback.return_value = True
        mock_tracker.is_correct_choice.return_value = True

        handler = CallbackHandler(tracker=mock_tracker, notifier=mock_notifier)
        callback_data = "provocation_123_choice_1"  # Format: provocation_{id}_choice_{index}

        mock_update = Mock()
        mock_update.callback_query.data = callback_data
        mock_update.callback_query.from_user.id = 12345
        mock_update.effective_chat.id = -1001234567890
        mock_update.callback_query.message.message_id = 67890
        mock_update.callback_query.message.edit_text = AsyncMock()
        mock_update.callback_query.answer = AsyncMock()

        mock_context = Mock()

        result = await handler.handle_callback(mock_update, mock_context)

        assert result is True
        mock_tracker.update_provocation_status.assert_called_once_with(
            123, "completed", response_user_id=12345
        )

    @pytest.mark.asyncio
    async def test_handles_incorrect_answer_callback(self, temp_config_dir: Path) -> None:
        """Should handle incorrect answer and schedule modlog notification."""
        from telegram_antilurk_bot.challenges.callback_handler import CallbackHandler

        handler = CallbackHandler()
        callback_data = "provocation_456_choice_2"

        mock_update = Mock()
        mock_update.callback_query.data = callback_data
        mock_update.callback_query.from_user.id = 12345
        mock_update.effective_chat.id = -1001234567890
        mock_update.callback_query.answer = AsyncMock()

        mock_context = Mock()

        with patch(
            "telegram_antilurk_bot.challenges.callback_handler.ProvocationTracker"
        ) as mock_tracker:
            with patch(
                "telegram_antilurk_bot.challenges.callback_handler.ModlogNotifier"
            ) as mock_notifier:
                mock_tracker_instance = AsyncMock()
                mock_tracker.return_value = mock_tracker_instance
                mock_notifier_instance = AsyncMock()
                mock_notifier.return_value = mock_notifier_instance

                # Mock incorrect answer
                mock_tracker_instance.validate_callback.return_value = True
                mock_tracker_instance.is_correct_choice.return_value = False

                result = await handler.handle_callback(mock_update, mock_context)

                assert result is True
                mock_tracker_instance.update_provocation_status.assert_called_once_with(
                    456, "failed", response_user_id=12345
                )
                mock_notifier_instance.schedule_kick_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_prevents_unauthorized_responses(self, temp_config_dir: Path) -> None:
        """Should prevent users from answering challenges for other users."""
        from telegram_antilurk_bot.challenges.callback_handler import CallbackHandler

        handler = CallbackHandler()
        callback_data = "provocation_789_choice_1"

        mock_update = Mock()
        mock_update.callback_query.data = callback_data
        mock_update.callback_query.from_user.id = 99999  # Different user
        mock_update.callback_query.answer = AsyncMock()

        mock_context = Mock()

        with patch(
            "telegram_antilurk_bot.challenges.callback_handler.ProvocationTracker"
        ) as mock_tracker:
            mock_tracker_instance = AsyncMock()
            mock_tracker.return_value = mock_tracker_instance

            # Mock validation failure (wrong user)
            mock_tracker_instance.validate_callback.return_value = False

            result = await handler.handle_callback(mock_update, mock_context)

            assert result is False
            mock_tracker_instance.update_provocation_status.assert_not_called()


class TestModlogNotifier:
    """Tests for sending notifications to modlog channels."""

    @pytest.mark.asyncio
    async def test_schedules_kick_notification_for_failed_challenge(
        self, temp_config_dir: Path
    ) -> None:
        """Should send kick notification to linked modlog channel."""
        from telegram_antilurk_bot.challenges.modlog_notifier import ModlogNotifier

        notifier = ModlogNotifier()
        provocation_id = 123

        with patch(
            "telegram_antilurk_bot.challenges.modlog_notifier.ProvocationTracker"
        ) as mock_tracker:
            with patch(
                "telegram_antilurk_bot.challenges.modlog_notifier.ConfigLoader"
            ) as mock_config:
                mock_tracker_instance = AsyncMock()
                mock_tracker.return_value = mock_tracker_instance

                # Mock provocation data
                mock_provocation = Mock()
                mock_provocation.chat_id = -1001234567890
                mock_provocation.user_id = 12345
                mock_provocation.puzzle_id = "test_puzzle"
                mock_tracker_instance.get_provocation.return_value = mock_provocation

                # Mock config with linked modlog
                mock_config_instance = Mock()
                mock_config.return_value = mock_config_instance
                mock_channels_config = Mock()
                mock_channels_config.get_linked_modlog.return_value = Mock(chat_id=-1009876543210)
                mock_config_instance.load_all.return_value = (Mock(), mock_channels_config, Mock())

                with patch(
                    "telegram_antilurk_bot.challenges.modlog_notifier.Application"
                ) as mock_app:
                    mock_bot = AsyncMock()
                    mock_app.builder().token().build.return_value.bot = mock_bot

                    await notifier.schedule_kick_notification(provocation_id)

                    # Should send notification to modlog
                    mock_bot.send_message.assert_called_once()
                    call_args = mock_bot.send_message.call_args
                    assert call_args.kwargs["chat_id"] == -1009876543210
                    assert "kick" in call_args.kwargs["text"].lower()

    @pytest.mark.asyncio
    async def test_includes_kick_confirmation_buttons(self, temp_config_dir: Path) -> None:
        """Should include confirmation buttons for manual kick action."""
        from telegram_antilurk_bot.challenges.modlog_notifier import ModlogNotifier

        notifier = ModlogNotifier()

        with patch(
            "telegram_antilurk_bot.challenges.modlog_notifier.ProvocationTracker"
        ) as mock_tracker:
            with patch(
                "telegram_antilurk_bot.challenges.modlog_notifier.ConfigLoader"
            ) as mock_config:
                with patch(
                    "telegram_antilurk_bot.challenges.modlog_notifier.Application"
                ) as mock_app:
                    # Setup mocks
                    mock_tracker_instance = AsyncMock()
                    mock_tracker.return_value = mock_tracker_instance

                    mock_provocation = Mock()
                    mock_provocation.chat_id = -1001234567890
                    mock_provocation.user_id = 12345
                    mock_tracker_instance.get_provocation.return_value = mock_provocation

                    mock_config_instance = Mock()
                    mock_config.return_value = mock_config_instance
                    mock_channels_config = Mock()
                    mock_channels_config.get_linked_modlog.return_value = Mock(
                        chat_id=-1009876543210
                    )
                    mock_config_instance.load_all.return_value = (
                        Mock(),
                        mock_channels_config,
                        Mock(),
                    )

                    mock_bot = AsyncMock()
                    mock_app.builder().token().build.return_value.bot = mock_bot

                    await notifier.schedule_kick_notification(123)

                    # Check that reply markup contains confirmation buttons
                    call_args = mock_bot.send_message.call_args
                    reply_markup = call_args.kwargs["reply_markup"]
                    assert isinstance(reply_markup, InlineKeyboardMarkup)

                    # Should have kick confirmation buttons
                    button_texts = [btn.text for row in reply_markup.inline_keyboard for btn in row]
                    assert any("kick" in text.lower() for text in button_texts)
                    assert any("confirm" in text.lower() or "✓" in text for text in button_texts)


class TestChallengeIntegration:
    """Integration tests for complete challenge flow."""

    @pytest.mark.asyncio
    async def test_complete_challenge_success_flow(self, temp_config_dir: Path) -> None:
        """Should handle complete successful challenge flow."""
        from telegram_antilurk_bot.challenges.challenge_engine import ChallengeEngine

        engine = ChallengeEngine()
        user = User(user_id=12345, username="testuser")
        chat_id = -1001234567890

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
            },
        ):
            # Mock all the dependencies
            with patch.multiple(
                "telegram_antilurk_bot.challenges.challenge_engine",
                ChallengeComposer=Mock(),
                ProvocationTracker=Mock(),
                CallbackHandler=Mock(),
            ):
                # Start challenge
                challenge_id = await engine.start_challenge(chat_id, user)
                assert isinstance(challenge_id, int)

                # Simulate correct response after some time
                await asyncio.sleep(0.1)  # Brief delay to simulate user response time

                success = await engine.handle_user_response(
                    challenge_id, user.user_id, correct=True
                )
                assert success is True

    @pytest.mark.asyncio
    async def test_complete_challenge_failure_flow(self, temp_config_dir: Path) -> None:
        """Should handle complete failed challenge flow with modlog notification."""
        from telegram_antilurk_bot.challenges.challenge_engine import ChallengeEngine

        engine = ChallengeEngine()
        user = User(user_id=67890, username="lurker")
        chat_id = -1001234567890

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
            },
        ):
            with patch.multiple(
                "telegram_antilurk_bot.challenges.challenge_engine",
                ChallengeComposer=Mock(),
                ProvocationTracker=Mock(),
                CallbackHandler=Mock(),
                ModlogNotifier=Mock(),
            ):
                # Access patched class via module to avoid patch.multiple return dict nuances
                from telegram_antilurk_bot.challenges import challenge_engine as _ce

                mock_notifier = _ce.ModlogNotifier

                # Start challenge
                challenge_id = await engine.start_challenge(chat_id, user)

                # Simulate incorrect response
                success = await engine.handle_user_response(
                    challenge_id, user.user_id, correct=False
                )
                assert success is True  # Handler executed successfully

                # Should trigger modlog notification
                mock_notifier.return_value.schedule_kick_notification.assert_called_once_with(
                    challenge_id
                )

    @pytest.mark.asyncio
    async def test_challenge_timeout_handling(self, temp_config_dir: Path) -> None:
        """Should handle challenge timeouts and send modlog notifications."""
        from telegram_antilurk_bot.challenges.challenge_engine import ChallengeEngine

        engine = ChallengeEngine()
        user = User(user_id=11111, username="silent_user")
        chat_id = -1001234567890

        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_TOKEN": "test_token",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
            },
        ):
            with patch.multiple(
                "telegram_antilurk_bot.challenges.challenge_engine",
                ChallengeComposer=Mock(),
                ProvocationTracker=Mock(),
                ModlogNotifier=Mock(),
            ):
                from telegram_antilurk_bot.challenges import challenge_engine as _ce

                mock_tracker = _ce.ProvocationTracker.return_value
                mock_notifier = _ce.ModlogNotifier.return_value

                # Mock expiration check
                mock_tracker.is_provocation_expired.return_value = True

                # Start challenge
                challenge_id = await engine.start_challenge(chat_id, user)

                # Process expired challenges
                await engine.process_expired_challenges()

                # Should update status and notify modlog
                mock_tracker.update_provocation_status.assert_called_with(challenge_id, "expired")
                mock_notifier.schedule_kick_notification.assert_called_once_with(challenge_id)
