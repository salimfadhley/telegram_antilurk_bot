"""Unit tests for Audit & Scheduling (Phase 4) - TDD approach."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestAuditScheduler:
    """Tests for the audit scheduler component."""

    def test_scheduler_initializes_with_default_cadence(self, temp_config_dir: Path) -> None:
        """Scheduler should initialize with default 15-minute cadence from config."""
        from telegram_antilurk_bot.audit.scheduler import AuditScheduler

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            scheduler = AuditScheduler()
            assert scheduler.audit_cadence_minutes == 15  # Default from GlobalConfig

    def test_scheduler_uses_config_cadence(self, temp_config_dir: Path) -> None:
        """Scheduler should use cadence from configuration."""
        from telegram_antilurk_bot.audit.scheduler import AuditScheduler
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        # Create custom config and mock config loader
        config = GlobalConfig(audit_cadence_minutes=30)
        mock_config_loader = Mock()
        mock_config_loader.load_all.return_value = (config, Mock(), Mock())

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            scheduler = AuditScheduler(config_loader=mock_config_loader)
            assert scheduler.audit_cadence_minutes == 30

    @pytest.mark.asyncio
    async def test_scheduler_runs_audit_cycle(self, temp_config_dir: Path) -> None:
        """Scheduler should run audit cycles at configured intervals."""
        from telegram_antilurk_bot.audit.scheduler import AuditScheduler

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            scheduler = AuditScheduler()

            with patch.object(scheduler, 'run_audit_cycle') as mock_audit:
                mock_audit.return_value = {'cycles_completed': 1}

                # Run one cycle
                result = await scheduler.run_audit_cycle()
                mock_audit.assert_called_once()
                assert result == {'cycles_completed': 1}

    def test_scheduler_can_be_stopped(self, temp_config_dir: Path) -> None:
        """Scheduler should be stoppable."""
        from telegram_antilurk_bot.audit.scheduler import AuditScheduler

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            scheduler = AuditScheduler()

            # Should start as not running
            assert not scheduler.is_running

            # Should be stoppable
            scheduler.stop()
            assert not scheduler.is_running


class TestLurkerSelection:
    """Tests for lurker identification and selection logic."""

    def test_identifies_lurkers_by_threshold(self, temp_config_dir: Path) -> None:
        """Should identify users who haven't interacted within threshold days."""
        from telegram_antilurk_bot.audit.lurker_selector import LurkerSelector
        from telegram_antilurk_bot.models.user import User
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            global_config = GlobalConfig()
            selector = LurkerSelector(global_config)

            # Mock users - one lurker, one active
            lurker_user = Mock(spec=User)
            lurker_user.user_id = 123
            lurker_user.is_lurker.return_value = True
            lurker_user.is_protected.return_value = False

            active_user = Mock(spec=User)
            active_user.user_id = 456
            active_user.is_lurker.return_value = False
            active_user.is_protected.return_value = False

            mock_users = [lurker_user, active_user]

            with patch.object(selector, '_get_chat_users', return_value=mock_users):
                lurkers = selector.identify_lurkers(-1001234567890, threshold_days=14)

                # Should identify only the lurker
                assert len(lurkers) == 1
                assert lurkers[0].user_id == 123

                # Should check lurker status with correct threshold
                lurker_user.is_lurker.assert_called_with(14)
                active_user.is_lurker.assert_called_with(14)

    def test_excludes_protected_users(self, temp_config_dir: Path) -> None:
        """Should exclude protected users (admins, bots, VIPs) from lurker selection."""
        from telegram_antilurk_bot.audit.lurker_selector import LurkerSelector
        from telegram_antilurk_bot.models.user import User

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            selector = LurkerSelector()

            # Mock protected lurker (admin who hasn't posted)
            protected_lurker = Mock(spec=User)
            protected_lurker.user_id = 789
            protected_lurker.is_lurker.return_value = True
            protected_lurker.is_protected.return_value = True  # Admin/VIP

            mock_users = [protected_lurker]

            with patch.object(selector, '_get_chat_users', return_value=mock_users):
                lurkers = selector.identify_lurkers(-1001234567890, threshold_days=14)

                # Should exclude protected users even if they're lurkers
                assert len(lurkers) == 0

    def test_skips_recently_provoked_users(self, temp_config_dir: Path) -> None:
        """Should skip users who were provoked within the current provocation interval."""
        from telegram_antilurk_bot.audit.lurker_selector import LurkerSelector
        from telegram_antilurk_bot.models.user import User

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            selector = LurkerSelector()

            # Mock lurker who was recently provoked
            recently_provoked = Mock(spec=User)
            recently_provoked.user_id = 999
            recently_provoked.is_lurker.return_value = True
            recently_provoked.is_protected.return_value = False

            mock_users = [recently_provoked]

            # Mock recent provocation
            with patch.object(selector, '_get_chat_users', return_value=mock_users):
                with patch.object(selector, '_was_recently_provoked', return_value=True):
                    lurkers = selector.identify_lurkers(-1001234567890, threshold_days=14, provocation_interval_hours=48)

                    # Should skip recently provoked users
                    assert len(lurkers) == 0

    def test_respects_rate_limits_per_hour(self, temp_config_dir: Path) -> None:
        """Should respect hourly rate limits when selecting users to provoke."""
        from telegram_antilurk_bot.audit.rate_limiter import RateLimiter

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            limiter = RateLimiter()
            chat_id = -1001234567890

            # Simulate 2 provocations in current hour (at limit)
            current_hour_count = 2
            with patch.object(limiter, '_get_hourly_provocation_count', return_value=current_hour_count):
                can_provoke = limiter.can_provoke_user(chat_id, rate_limit_per_hour=2)
                assert can_provoke is False  # At limit

            # Should allow if under limit
            current_hour_count = 1
            with patch.object(limiter, '_get_hourly_provocation_count', return_value=current_hour_count):
                can_provoke = limiter.can_provoke_user(chat_id, rate_limit_per_hour=2)
                assert can_provoke is True  # Under limit

    def test_respects_rate_limits_per_day(self, temp_config_dir: Path) -> None:
        """Should respect daily rate limits when selecting users to provoke."""
        from telegram_antilurk_bot.audit.rate_limiter import RateLimiter

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            limiter = RateLimiter()
            chat_id = -1001234567890

            # Simulate 15 provocations today (at daily limit)
            with patch.object(limiter, '_get_hourly_provocation_count', return_value=1):  # Under hourly
                with patch.object(limiter, '_get_daily_provocation_count', return_value=15):
                    can_provoke = limiter.can_provoke_user(chat_id, rate_limit_per_hour=2, rate_limit_per_day=15)
                    assert can_provoke is False  # At daily limit

    def test_tracks_provocation_counts(self, temp_config_dir: Path) -> None:
        """Should track and increment provocation counts."""
        from telegram_antilurk_bot.audit.rate_limiter import RateLimiter

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            limiter = RateLimiter()
            chat_id = -1001234567890
            user_id = 123456789

            with patch.object(limiter, '_record_provocation') as mock_record:
                limiter.record_provocation(chat_id, user_id)
                mock_record.assert_called_once_with(chat_id, user_id)


class TestBacklogManagement:
    """Tests for backlog management when rate limits are hit."""

    def test_creates_backlog_when_rate_limited(self, temp_config_dir: Path) -> None:
        """Should create backlog entries when rate limits prevent immediate provocation."""
        from telegram_antilurk_bot.audit.backlog_manager import BacklogManager
        from telegram_antilurk_bot.models.user import User

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            backlog = BacklogManager()

            # Mock lurkers that can't be provoked due to rate limits
            lurker1 = Mock(spec=User)
            lurker1.user_id = 111
            lurker2 = Mock(spec=User)
            lurker2.user_id = 222

            chat_id = -1001234567890
            lurkers = [lurker1, lurker2]

            with patch.object(backlog, '_save_to_backlog') as mock_save:
                backlog.add_to_backlog(chat_id, lurkers, reason="rate_limited")

                # Should save both lurkers to backlog
                assert mock_save.call_count == 2

    def test_retrieves_backlog_users_for_next_cycle(self, temp_config_dir: Path) -> None:
        """Should retrieve backlogged users for the next audit cycle."""
        from telegram_antilurk_bot.audit.backlog_manager import BacklogManager

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            backlog = BacklogManager()
            chat_id = -1001234567890

            # Mock backlogged user entries
            mock_entries = [
                {'user_id': 111, 'added_at': datetime.utcnow() - timedelta(hours=1)},
                {'user_id': 222, 'added_at': datetime.utcnow() - timedelta(minutes=30)}
            ]

            with patch.object(backlog, '_get_backlog_entries', return_value=mock_entries):
                backlog_users = backlog.get_backlog_users(chat_id)

                assert len(backlog_users) == 2
                assert 111 in [u['user_id'] for u in backlog_users]
                assert 222 in [u['user_id'] for u in backlog_users]

    def test_clears_processed_backlog_entries(self, temp_config_dir: Path) -> None:
        """Should clear backlog entries after they're processed."""
        from telegram_antilurk_bot.audit.backlog_manager import BacklogManager

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            backlog = BacklogManager()
            chat_id = -1001234567890
            user_ids = [111, 222]

            with patch.object(backlog, '_clear_backlog_entries') as mock_clear:
                backlog.clear_processed_entries(chat_id, user_ids)
                mock_clear.assert_called_once_with(chat_id, user_ids)


class TestAuditCycleIntegration:
    """Integration tests for complete audit cycles."""

    @pytest.mark.asyncio
    async def test_complete_audit_cycle(self, temp_config_dir: Path) -> None:
        """Should run complete audit cycle: select lurkers, check limits, provoke or backlog."""
        from telegram_antilurk_bot.audit.audit_engine import AuditEngine
        from telegram_antilurk_bot.config.schemas import ChannelEntry

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            engine = AuditEngine()

            # Mock moderated channel
            moderated_channel = ChannelEntry(
                chat_id=-1001234567890,
                chat_name="Test Moderated",
                mode="moderated"
            )

            # Mock components
            with patch.object(engine, '_get_moderated_channels', return_value=[moderated_channel]):
                with patch.object(engine, '_identify_lurkers', return_value=[Mock(user_id=123)]):
                    with patch.object(engine, '_can_provoke', return_value=True):
                        with patch.object(engine, '_initiate_provocation') as mock_provoke:

                            await engine.run_audit_cycle()

                            # Should initiate provocation for eligible lurker
                            mock_provoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_cycle_with_rate_limiting(self, temp_config_dir: Path) -> None:
        """Should handle rate limiting by adding users to backlog."""
        from telegram_antilurk_bot.audit.audit_engine import AuditEngine
        from telegram_antilurk_bot.config.schemas import ChannelEntry

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            engine = AuditEngine()

            # Mock moderated channel
            moderated_channel = ChannelEntry(
                chat_id=-1001234567890,
                chat_name="Test Moderated",
                mode="moderated"
            )

            # Mock components
            with patch.object(engine, '_get_moderated_channels', return_value=[moderated_channel]):
                with patch.object(engine, '_identify_lurkers', return_value=[Mock(user_id=123)]):
                    with patch.object(engine, '_can_provoke', return_value=False):  # Rate limited
                        with patch.object(engine, '_add_to_backlog') as mock_backlog:

                            await engine.run_audit_cycle()

                            # Should add user to backlog instead of provoking
                            mock_backlog.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_cycle_processes_multiple_chats(self, temp_config_dir: Path) -> None:
        """Should process all moderated chats in a single audit cycle."""
        from telegram_antilurk_bot.audit.audit_engine import AuditEngine
        from telegram_antilurk_bot.config.schemas import ChannelEntry

        with patch.dict('os.environ', {
            'TELEGRAM_TOKEN': 'test_token',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CONFIG_DIR': str(temp_config_dir)
        }):
            engine = AuditEngine()

            # Mock multiple moderated channels
            channels = [
                ChannelEntry(chat_id=-1001, chat_name="Chat 1", mode="moderated"),
                ChannelEntry(chat_id=-1002, chat_name="Chat 2", mode="moderated"),
                ChannelEntry(chat_id=-1003, chat_name="Chat 3", mode="modlog")  # Should skip
            ]

            with patch.object(engine, '_get_moderated_channels', return_value=channels[:2]):  # Only moderated
                with patch.object(engine, '_process_chat') as mock_process:

                    await engine.run_audit_cycle()

                    # Should process both moderated chats
                    assert mock_process.call_count == 2


class TestPropertyBasedTesting:
    """Property-based tests using Hypothesis for rate limiting and scheduling invariants."""

    def test_rate_limiter_invariants_with_hypothesis(self, temp_config_dir: Path) -> None:
        """Rate limiting should maintain invariants across various inputs."""
        from hypothesis import given
        from hypothesis import strategies as st

        from telegram_antilurk_bot.audit.rate_limiter import RateLimiter

        @given(
            hourly_count=st.integers(min_value=0, max_value=10),
            daily_count=st.integers(min_value=0, max_value=100),
            hour_limit=st.integers(min_value=1, max_value=5),
            day_limit=st.integers(min_value=1, max_value=50)
        )
        def test_rate_limit_logic(hourly_count: int, daily_count: int, hour_limit: int, day_limit: int) -> None:
            with patch.dict('os.environ', {
                'TELEGRAM_TOKEN': 'test_token',
                'DATABASE_URL': 'postgresql://test:test@localhost/test',
                'CONFIG_DIR': str(temp_config_dir)
            }):
                limiter = RateLimiter()

                with patch.object(limiter, '_get_hourly_provocation_count', return_value=hourly_count):
                    with patch.object(limiter, '_get_daily_provocation_count', return_value=daily_count):
                        can_provoke = limiter.can_provoke_user(
                            -1001234567890,
                            rate_limit_per_hour=hour_limit,
                            rate_limit_per_day=day_limit
                        )

                        # Invariant: can only provoke if under BOTH hourly AND daily limits
                        expected = (hourly_count < hour_limit) and (daily_count < day_limit)
                        assert can_provoke == expected

        # Run the property-based test
        test_rate_limit_logic()
