"""Unit tests for database models - TDD approach."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """User model should store user information."""
        from telegram_antilurk_bot.models.user import User

        user = User(
            user_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )

        assert user.user_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.first_seen is not None
        assert user.last_seen is not None
        assert user.last_interaction_at is not None

    def test_user_update_last_seen(self):
        """User should update last_seen timestamp."""
        from telegram_antilurk_bot.models.user import User

        user = User(user_id=123)
        initial_time = user.last_seen

        # Mock time passing
        import time
        time.sleep(0.01)

        user.update_last_seen()

        assert user.last_seen > initial_time
        assert user.last_interaction_at == initial_time  # Should not change

    def test_user_update_interaction(self):
        """User should update both timestamps on interaction."""
        from telegram_antilurk_bot.models.user import User

        user = User(user_id=123)
        initial_seen = user.last_seen
        initial_interaction = user.last_interaction_at

        # Mock time passing
        import time
        time.sleep(0.01)

        user.update_interaction()

        assert user.last_seen > initial_seen
        assert user.last_interaction_at > initial_interaction

    def test_user_is_lurker(self):
        """User should be identified as lurker based on threshold."""
        from telegram_antilurk_bot.models.user import User

        # Create user with old interaction
        user = User(user_id=123)
        user.last_interaction_at = datetime.utcnow() - timedelta(days=20)

        # Test with different thresholds
        assert user.is_lurker(14) is True  # 20 days > 14 days
        assert user.is_lurker(30) is False  # 20 days < 30 days

        # Test with recent interaction
        user.last_interaction_at = datetime.utcnow() - timedelta(days=5)
        assert user.is_lurker(14) is False  # 5 days < 14 days

    def test_user_is_protected(self):
        """User should be protected based on flags and roles."""
        from telegram_antilurk_bot.models.user import User

        # Regular user - not protected
        user = User(user_id=123)
        assert user.is_protected() is False

        # Admin user - protected
        user.flags = {"is_admin": True}
        assert user.is_protected() is True

        # Bot user - protected
        user.flags = {"is_bot": True}
        assert user.is_protected() is True

        # User with protected role
        user.flags = {}
        user.roles = ["moderator"]
        assert user.is_protected() is True

        # User with mixed roles
        user.roles = ["regular", "vip"]
        assert user.is_protected() is True


class TestMessageArchiveModel:
    """Tests for MessageArchive model."""

    def test_message_archive_creation(self):
        """MessageArchive should store message data."""
        from telegram_antilurk_bot.models.message import MessageArchive

        message = MessageArchive(
            chat_id=-1001234567890,
            message_id=999,
            user_id=123456789,
            text="Hello, world!",
            message_type="text",
            sent_at=datetime.utcnow()
        )

        assert message.chat_id == -1001234567890
        assert message.message_id == 999
        assert message.user_id == 123456789
        assert message.text == "Hello, world!"
        assert message.message_type == "text"
        assert message.sent_at is not None
        assert message.archived_at is not None

    def test_message_is_reply(self):
        """MessageArchive should identify reply messages."""
        from telegram_antilurk_bot.models.message import MessageArchive

        # Regular message
        message = MessageArchive(
            chat_id=1,
            message_id=1,
            user_id=1,
            sent_at=datetime.utcnow()
        )
        assert message.is_reply is False

        # Reply message
        message.reply_to_message_id = 100
        assert message.is_reply is True

    def test_message_is_forward(self):
        """MessageArchive should identify forwarded messages."""
        from telegram_antilurk_bot.models.message import MessageArchive

        # Regular message
        message = MessageArchive(
            chat_id=1,
            message_id=1,
            user_id=1,
            sent_at=datetime.utcnow()
        )
        assert message.is_forward is False

        # Forwarded message
        message.forward_from_chat_id = -1009876543210
        assert message.is_forward is True


class TestProvocationModel:
    """Tests for Provocation model."""

    def test_provocation_creation(self):
        """Provocation should store challenge data."""
        from telegram_antilurk_bot.models.provocation import Provocation, ProvocationOutcome

        expires = datetime.utcnow() + timedelta(hours=48)
        provocation = Provocation(
            chat_id=-1001234567890,
            user_id=123456789,
            puzzle_id="test_001",
            puzzle_question="What is 2 + 2?",
            correct_answer="4",
            expires_at=expires
        )

        assert provocation.chat_id == -1001234567890
        assert provocation.user_id == 123456789
        assert provocation.puzzle_id == "test_001"
        assert provocation.puzzle_question == "What is 2 + 2?"
        assert provocation.correct_answer == "4"
        assert provocation.outcome == ProvocationOutcome.PENDING
        assert provocation.expires_at == expires

    def test_provocation_is_expired(self):
        """Provocation should detect expiration."""
        from telegram_antilurk_bot.models.provocation import Provocation

        # Not expired
        provocation = Provocation(
            chat_id=1,
            user_id=1,
            puzzle_id="p1",
            puzzle_question="Q?",
            correct_answer="A",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert provocation.is_expired is False

        # Expired
        provocation.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert provocation.is_expired is True

    def test_provocation_mark_sent(self):
        """Provocation should track when sent."""
        from telegram_antilurk_bot.models.provocation import Provocation

        provocation = Provocation(
            chat_id=1,
            user_id=1,
            puzzle_id="p1",
            puzzle_question="Q?",
            correct_answer="A",
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )

        assert provocation.sent_at is None
        assert provocation.challenge_message_id is None

        provocation.mark_sent(message_id=12345)

        assert provocation.sent_at is not None
        assert provocation.challenge_message_id == 12345

    def test_provocation_mark_responded(self):
        """Provocation should track responses."""
        from telegram_antilurk_bot.models.provocation import Provocation, ProvocationOutcome

        provocation = Provocation(
            chat_id=1,
            user_id=1,
            puzzle_id="p1",
            puzzle_question="Q?",
            correct_answer="A",
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )

        # Correct answer
        provocation.mark_responded("A", is_correct=True)
        assert provocation.responded_at is not None
        assert provocation.user_answer == "A"
        assert provocation.outcome == ProvocationOutcome.CORRECT

        # Reset for incorrect answer test
        provocation.responded_at = None
        provocation.outcome = ProvocationOutcome.PENDING

        # Incorrect answer
        provocation.mark_responded("B", is_correct=False)
        assert provocation.responded_at is not None
        assert provocation.user_answer == "B"
        assert provocation.outcome == ProvocationOutcome.INCORRECT

    def test_provocation_mark_timeout(self):
        """Provocation should handle timeouts."""
        from telegram_antilurk_bot.models.provocation import Provocation, ProvocationOutcome

        provocation = Provocation(
            chat_id=1,
            user_id=1,
            puzzle_id="p1",
            puzzle_question="Q?",
            correct_answer="A",
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )

        provocation.mark_timeout()
        assert provocation.outcome == ProvocationOutcome.TIMEOUT

    def test_provocation_mark_cancelled(self):
        """Provocation should handle cancellation."""
        from telegram_antilurk_bot.models.provocation import Provocation, ProvocationOutcome

        provocation = Provocation(
            chat_id=1,
            user_id=1,
            puzzle_id="p1",
            puzzle_question="Q?",
            correct_answer="A",
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )

        provocation.mark_cancelled()
        assert provocation.outcome == ProvocationOutcome.CANCELLED


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_get_db_url(self):
        """Should get database URL from environment."""
        from telegram_antilurk_bot.models.base import get_db_url
        import os

        # Test with postgres:// format
        os.environ['DATABASE_URL'] = 'postgres://user:pass@host:5432/db'
        url = get_db_url()
        assert url == 'postgresql://user:pass@host:5432/db'

        # Test with postgresql:// format
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@host:5432/db'
        url = get_db_url()
        assert url == 'postgresql://user:pass@host:5432/db'

    def test_get_db_url_missing(self):
        """Should raise error if DATABASE_URL is not set."""
        from telegram_antilurk_bot.models.base import get_db_url
        import os

        # Remove DATABASE_URL if it exists
        original = os.environ.pop('DATABASE_URL', None)
        try:
            with pytest.raises(ValueError) as exc_info:
                get_db_url()
            assert "DATABASE_URL" in str(exc_info.value)
        finally:
            # Restore original value
            if original:
                os.environ['DATABASE_URL'] = original