"""Unit tests for Message & Event Logging - TDD approach for Phase 6."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestMessageArchiver:
    """Tests for message archiving functionality."""

    @pytest.mark.asyncio
    async def test_archives_text_message_with_metadata(self, temp_config_dir: Path) -> None:
        """Should archive text messages with full metadata."""
        from telegram_antilurk_bot.logging.message_archiver import MessageArchiver

        archiver = MessageArchiver()

        mock_update = Mock()
        mock_update.message.message_id = 12345
        mock_update.message.chat.id = -1001234567890
        mock_update.message.from_user.id = 67890
        mock_update.message.from_user.is_bot = False
        mock_update.message.from_user.username = "testuser"
        mock_update.message.from_user.first_name = "Test"
        mock_update.message.from_user.last_name = "User"
        mock_update.message.text = "Hello, this is a test message!"
        mock_update.message.date = datetime.utcnow()

        # Mock the configuration to return this as a moderated chat
        mock_config_loader = Mock()
        mock_channels_config = Mock()
        mock_channel_entry = Mock()
        mock_channel_entry.chat_id = -1001234567890
        mock_channels_config.get_moderated_channels.return_value = [mock_channel_entry]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())

        archiver.config_loader = mock_config_loader

        archived_message = await archiver.archive_message(mock_update)

        assert archived_message is not None
        assert archived_message.message_id == 12345
        assert archived_message.chat_id == -1001234567890
        assert archived_message.user_id == 67890
        assert archived_message.message_text == "Hello, this is a test message!"
        assert archived_message.message_type == "text"

    @pytest.mark.asyncio
    async def test_handles_different_message_types(self, temp_config_dir: Path) -> None:
        """Should handle various message types (photo, sticker, etc.)."""
        from telegram_antilurk_bot.logging.message_archiver import MessageArchiver

        archiver = MessageArchiver()

        # Test photo message
        mock_photo_update = Mock()
        mock_photo_update.message.message_id = 11111
        mock_photo_update.message.chat.id = -1001234567890
        mock_photo_update.message.from_user.id = 67890
        mock_photo_update.message.text = None
        mock_photo_update.message.photo = [Mock()]
        mock_photo_update.message.caption = "Photo caption"
        mock_photo_update.message.date = datetime.utcnow()

        photo_archive = await archiver.archive_message(mock_photo_update)

        assert photo_archive.message_type == "photo"
        assert photo_archive.message_text == "Photo caption"

        # Test sticker message
        mock_sticker_update = Mock()
        mock_sticker_update.message.message_id = 22222
        mock_sticker_update.message.chat.id = -1001234567890
        mock_sticker_update.message.from_user.id = 67890
        mock_sticker_update.message.text = None
        mock_sticker_update.message.photo = None
        mock_sticker_update.message.sticker = Mock()
        mock_sticker_update.message.sticker.emoji = "😀"
        mock_sticker_update.message.date = datetime.utcnow()

        sticker_archive = await archiver.archive_message(mock_sticker_update)

        assert sticker_archive.message_type == "sticker"
        assert sticker_archive.message_text == "😀"

    @pytest.mark.asyncio
    async def test_updates_user_last_interaction_timestamp(self, temp_config_dir: Path) -> None:
        """Should update user's last interaction timestamp when archiving."""
        from telegram_antilurk_bot.logging.message_archiver import MessageArchiver

        archiver = MessageArchiver()

        mock_update = Mock()
        mock_update.message.message_id = 33333
        mock_update.message.chat.id = -1001234567890
        mock_update.message.from_user.id = 67890
        mock_update.message.text = "Activity message"
        mock_update.message.date = datetime.utcnow()

        with patch('telegram_antilurk_bot.logging.message_archiver.UserTracker') as mock_tracker:
            mock_tracker_instance = AsyncMock()
            mock_tracker.return_value = mock_tracker_instance

            await archiver.archive_message(mock_update)

            # Should update user's last interaction
            mock_tracker_instance.update_user_activity.assert_called_once_with(
                user_id=67890,
                chat_id=-1001234567890,
                timestamp=mock_update.message.date
            )

    @pytest.mark.asyncio
    async def test_ignores_bot_messages(self, temp_config_dir: Path) -> None:
        """Should not archive messages from bots."""
        from telegram_antilurk_bot.logging.message_archiver import MessageArchiver

        archiver = MessageArchiver()

        mock_bot_update = Mock()
        mock_bot_update.message.from_user.is_bot = True
        mock_bot_update.message.text = "Bot message"

        result = await archiver.archive_message(mock_bot_update)

        assert result is None  # Should not archive bot messages

    @pytest.mark.asyncio
    async def test_filters_by_moderated_chats_only(self, temp_config_dir: Path) -> None:
        """Should only archive messages from moderated chats."""
        from telegram_antilurk_bot.logging.message_archiver import MessageArchiver

        archiver = MessageArchiver()

        mock_update = Mock()
        mock_update.message.chat.id = -1009999999999  # Not a moderated chat
        mock_update.message.from_user.id = 67890
        mock_update.message.from_user.is_bot = False
        mock_update.message.text = "Message from non-moderated chat"

        with patch('telegram_antilurk_bot.logging.message_archiver.ConfigLoader') as mock_config:
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            mock_channels_config = Mock()
            mock_channels_config.get_moderated_channels.return_value = []  # No moderated chats
            mock_config_instance.load_all.return_value = (Mock(), mock_channels_config, Mock())

            result = await archiver.archive_message(mock_update)

            assert result is None  # Should not archive from non-moderated chat


class TestUserTracker:
    """Tests for user activity tracking."""

    @pytest.mark.asyncio
    async def test_creates_new_user_on_first_message(self, temp_config_dir: Path) -> None:
        """Should create new user record on first message."""
        from telegram_antilurk_bot.logging.user_tracker import UserTracker

        tracker = UserTracker()

        user_data = {
            'id': 12345,
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'is_bot': False
        }

        mock_telegram_user = Mock()
        for key, value in user_data.items():
            setattr(mock_telegram_user, key, value)

        chat_id = -1001234567890
        timestamp = datetime.utcnow()

        user = await tracker.update_user_activity(
            user_id=12345,
            chat_id=chat_id,
            timestamp=timestamp,
            telegram_user=mock_telegram_user
        )

        assert user is not None
        assert user.user_id == 12345
        assert user.username == 'newuser'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.last_message_at == timestamp

    @pytest.mark.asyncio
    async def test_updates_existing_user_timestamp(self, temp_config_dir: Path) -> None:
        """Should update existing user's last message timestamp."""
        from telegram_antilurk_bot.logging.user_tracker import UserTracker

        tracker = UserTracker()

        # First message
        first_timestamp = datetime.utcnow() - timedelta(hours=1)
        await tracker.update_user_activity(
            user_id=67890,
            chat_id=-1001234567890,
            timestamp=first_timestamp
        )

        # Second message (more recent)
        second_timestamp = datetime.utcnow()
        user2 = await tracker.update_user_activity(
            user_id=67890,
            chat_id=-1001234567890,
            timestamp=second_timestamp
        )

        assert user2.last_message_at == second_timestamp
        assert user2.last_message_at > first_timestamp

    @pytest.mark.asyncio
    async def test_tracks_user_join_date(self, temp_config_dir: Path) -> None:
        """Should track when user first joined the system."""
        from telegram_antilurk_bot.logging.user_tracker import UserTracker

        tracker = UserTracker()

        join_time = datetime.utcnow()
        user = await tracker.update_user_activity(
            user_id=11111,
            chat_id=-1001234567890,
            timestamp=join_time
        )

        assert user.join_date is not None
        # Join date should be close to the timestamp
        assert abs((user.join_date - join_time).total_seconds()) < 5


class TestProvocationLogger:
    """Tests for provocation lifecycle logging."""

    @pytest.mark.asyncio
    async def test_logs_provocation_creation(self, temp_config_dir: Path) -> None:
        """Should log when provocations are created."""
        from telegram_antilurk_bot.logging.provocation_logger import ProvocationLogger

        logger = ProvocationLogger()

        provocation_data = {
            'provocation_id': 123,
            'chat_id': -1001234567890,
            'user_id': 67890,
            'puzzle_id': 'math_001',
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=30)
        }

        await logger.log_provocation_created(**provocation_data)

        # Verify log entry was created
        entries = await logger.get_provocation_history(provocation_data['provocation_id'])
        assert len(entries) == 1
        assert entries[0]['event'] == 'created'
        assert entries[0]['provocation_id'] == 123

    @pytest.mark.asyncio
    async def test_logs_provocation_responses(self, temp_config_dir: Path) -> None:
        """Should log user responses to provocations."""
        from telegram_antilurk_bot.logging.provocation_logger import ProvocationLogger

        logger = ProvocationLogger()

        provocation_id = 456
        response_data = {
            'provocation_id': provocation_id,
            'user_id': 67890,
            'response_time': datetime.utcnow(),
            'choice_selected': 2,
            'is_correct': True
        }

        await logger.log_provocation_response(**response_data)

        entries = await logger.get_provocation_history(provocation_id)
        response_entry = next((e for e in entries if e['event'] == 'response'), None)

        assert response_entry is not None
        assert response_entry['choice_selected'] == 2
        assert response_entry['is_correct'] is True

    @pytest.mark.asyncio
    async def test_logs_provocation_expiration(self, temp_config_dir: Path) -> None:
        """Should log when provocations expire without response."""
        from telegram_antilurk_bot.logging.provocation_logger import ProvocationLogger

        logger = ProvocationLogger()

        provocation_id = 789
        expiration_data = {
            'provocation_id': provocation_id,
            'expired_at': datetime.utcnow(),
            'final_status': 'expired'
        }

        await logger.log_provocation_expired(**expiration_data)

        entries = await logger.get_provocation_history(provocation_id)
        expiry_entry = next((e for e in entries if e['event'] == 'expired'), None)

        assert expiry_entry is not None
        assert expiry_entry['final_status'] == 'expired'

    @pytest.mark.asyncio
    async def test_provides_rate_limiting_data(self, temp_config_dir: Path) -> None:
        """Should provide data for rate limiting calculations."""
        from telegram_antilurk_bot.logging.provocation_logger import ProvocationLogger

        logger = ProvocationLogger()

        chat_id = -1001234567890
        current_time = datetime.utcnow()

        # Log multiple provocations for rate limiting test
        for i in range(3):
            await logger.log_provocation_created(
                provocation_id=1000 + i,
                chat_id=chat_id,
                user_id=67890 + i,
                puzzle_id=f'test_{i}',
                created_at=current_time - timedelta(minutes=i * 15)
            )

        # Get provocation count for last hour
        hourly_count = await logger.get_provocation_count_since(
            chat_id=chat_id,
            since=current_time - timedelta(hours=1)
        )

        assert hourly_count >= 3  # Should include all recent provocations


class TestNATSEventPublisher:
    """Tests for optional NATS event publishing."""

    @pytest.mark.asyncio
    async def test_publishes_events_when_nats_enabled(self, temp_config_dir: Path) -> None:
        """Should publish events to NATS when NATS_URL is configured."""
        from telegram_antilurk_bot.logging.nats_publisher import NATSEventPublisher

        with patch.dict('os.environ', {'NATS_URL': 'nats://localhost:4222'}):
            publisher = NATSEventPublisher()

            event_data = {
                'event_type': 'challenge_failed',
                'chat_id': -1001234567890,
                'user_id': 67890,
                'provocation_id': 123,
                'timestamp': datetime.utcnow().isoformat()
            }

            with patch('telegram_antilurk_bot.logging.nats_publisher.nats') as mock_nats:
                mock_client = AsyncMock()
                mock_nats.connect.return_value = mock_client

                await publisher.publish_event('antilurk.challenge.failed', event_data)

                mock_nats.connect.assert_called_once_with('nats://localhost:4222')
                mock_client.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_publishing_when_nats_disabled(self, temp_config_dir: Path) -> None:
        """Should skip publishing when NATS_URL is not configured."""
        from telegram_antilurk_bot.logging.nats_publisher import NATSEventPublisher

        # No NATS_URL environment variable
        publisher = NATSEventPublisher()

        event_data = {'test': 'data'}

        # Should not attempt to connect to NATS
        with patch('telegram_antilurk_bot.logging.nats_publisher.nats') as mock_nats:
            await publisher.publish_event('test.subject', event_data)
            mock_nats.connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_nats_connection_failures_gracefully(self, temp_config_dir: Path) -> None:
        """Should handle NATS connection failures without crashing."""
        from telegram_antilurk_bot.logging.nats_publisher import NATSEventPublisher

        with patch.dict('os.environ', {'NATS_URL': 'nats://invalid:4222'}):
            publisher = NATSEventPublisher()

            with patch('telegram_antilurk_bot.logging.nats_publisher.nats') as mock_nats:
                mock_nats.connect.side_effect = Exception("Connection failed")

                # Should not raise exception
                try:
                    await publisher.publish_event('test.subject', {'test': 'data'})
                except Exception:
                    pytest.fail("Should handle NATS connection failures gracefully")


class TestMessageLoggingIntegration:
    """Integration tests for complete message logging flow."""

    @pytest.mark.asyncio
    async def test_complete_message_processing_flow(self, temp_config_dir: Path) -> None:
        """Should handle complete message processing from ingestion to archiving."""
        from telegram_antilurk_bot.logging.message_processor import MessageProcessor

        processor = MessageProcessor()

        mock_update = Mock()
        mock_update.message.message_id = 99999
        mock_update.message.chat.id = -1001234567890
        mock_update.message.from_user.id = 55555
        mock_update.message.from_user.username = 'testuser'
        mock_update.message.from_user.first_name = 'Test'
        mock_update.message.from_user.is_bot = False
        mock_update.message.text = "Integration test message"
        mock_update.message.date = datetime.utcnow()

        with patch.multiple(
            'telegram_antilurk_bot.logging.message_processor',
            MessageArchiver=Mock(),
            UserTracker=Mock(),
            NATSEventPublisher=Mock()
        ) as mocks:
            mock_archiver = mocks['MessageArchiver'].return_value
            mock_tracker = mocks['UserTracker'].return_value
            mock_publisher = mocks['NATSEventPublisher'].return_value

            mock_archiver.archive_message = AsyncMock(return_value=Mock())
            mock_tracker.update_user_activity = AsyncMock(return_value=Mock())
            mock_publisher.publish_event = AsyncMock()

            result = await processor.process_message(mock_update)

            assert result is True

            # All components should be called
            mock_archiver.archive_message.assert_called_once_with(mock_update)
            mock_tracker.update_user_activity.assert_called_once()
            mock_publisher.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_view_updates_with_message_activity(self, temp_config_dir: Path) -> None:
        """Should update user_channel_activity view when processing messages."""
        from telegram_antilurk_bot.logging.view_updater import ViewUpdater

        updater = ViewUpdater()

        user_id = 77777
        chat_id = -1001234567890
        message_count = 5

        # Simulate multiple messages from user
        for i in range(message_count):
            await updater.record_user_activity(
                user_id=user_id,
                chat_id=chat_id,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )

        # Check view reflects activity
        activity_stats = await updater.get_user_channel_activity(user_id, chat_id)

        assert activity_stats is not None
        assert activity_stats['user_id'] == user_id
        assert activity_stats['chat_id'] == chat_id
        assert activity_stats['message_count'] >= message_count

    @pytest.mark.asyncio
    async def test_provocation_lifecycle_complete_logging(self, temp_config_dir: Path) -> None:
        """Should log complete provocation lifecycle from creation to resolution."""
        from telegram_antilurk_bot.logging.lifecycle_logger import LifecycleLogger

        logger = LifecycleLogger()

        provocation_id = 888
        chat_id = -1001234567890
        user_id = 99999

        # Log creation
        await logger.log_provocation_created(
            provocation_id=provocation_id,
            chat_id=chat_id,
            user_id=user_id,
            puzzle_id='lifecycle_test'
        )

        # Log response
        await logger.log_provocation_response(
            provocation_id=provocation_id,
            user_id=user_id,
            is_correct=False
        )

        # Log modlog notification
        await logger.log_modlog_notification_sent(
            provocation_id=provocation_id,
            modlog_chat_id=-1009876543210
        )

        # Get complete history
        history = await logger.get_complete_history(provocation_id)

        assert len(history) == 3
        events = [entry['event'] for entry in history]
        assert 'created' in events
        assert 'response' in events
        assert 'modlog_notified' in events
