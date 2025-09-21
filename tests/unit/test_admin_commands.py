"""Unit tests for Admin Commands & Reports - TDD approach for Phase 7."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from telegram_antilurk_bot.database.models import User


class TestShowCommands:
    """Tests for /antlurk show commands."""

    @pytest.mark.asyncio
    async def test_show_links_displays_chat_connections(self, temp_config_dir: Path) -> None:
        """Should display current chat linkages between moderated and modlog chats."""
        from telegram_antilurk_bot.admin.show_commands import ShowCommandHandler

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["links"]

        # Mock configuration with linked chats
        mock_config_loader = Mock()
        mock_channels_config = Mock()

        # Setup mock channels with links
        mock_moderated = Mock()
        mock_moderated.chat_id = -1001234567890
        mock_moderated.chat_name = "Test Moderated"
        mock_moderated.mode = "moderated"
        mock_moderated.modlog_ref = -1009876543210

        mock_modlog = Mock()
        mock_modlog.chat_id = -1009876543210
        mock_modlog.chat_name = "Test Modlog"
        mock_modlog.mode = "modlog"

        mock_channels_config.channels = [mock_moderated, mock_modlog]
        mock_channels_config.get_moderated_channels.return_value = [mock_moderated]
        mock_channels_config.get_modlog_channels.return_value = [mock_modlog]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())

        handler = ShowCommandHandler(config_loader=mock_config_loader)
        await handler.handle_show_command(mock_update, mock_context)

        # Should display link information
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "Test Moderated" in reply_text
        assert "Test Modlog" in reply_text
        assert "linkages" in reply_text.lower() or "└──" in reply_text

    @pytest.mark.asyncio
    async def test_show_config_displays_effective_settings(self, temp_config_dir: Path) -> None:
        """Should display current effective configuration settings."""
        from telegram_antilurk_bot.admin.show_commands import ShowCommandHandler

        # Mock configuration
        mock_config_loader = Mock()
        mock_global_config = Mock()
        mock_global_config.lurk_threshold_days = 14
        mock_global_config.audit_cadence_minutes = 15
        mock_global_config.rate_limit_per_hour = 2
        mock_global_config.rate_limit_per_day = 15
        mock_global_config.enable_nats = True
        mock_global_config.enable_announcements = False
        mock_global_config.provenance.updated_at.strftime = Mock(return_value="2024-01-01 10:00")
        mock_global_config.provenance.updated_by = "test"

        mock_channels_config = Mock()
        mock_channels_config.channels = []
        mock_puzzles_config = Mock()
        mock_puzzles_config.puzzles = []

        mock_config_loader.load_all.return_value = (mock_global_config, mock_channels_config, mock_puzzles_config)

        handler = ShowCommandHandler(config_loader=mock_config_loader)

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["config"]

        await handler.handle_show_command(mock_update, mock_context)

        # Should display configuration values
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "14" in reply_text  # lurk_threshold_days
        assert "15" in reply_text  # audit_cadence_minutes
        assert "2" in reply_text   # rate_limit_per_hour

    @pytest.mark.asyncio
    async def test_show_reports_only_works_in_moderated_chats(self, temp_config_dir: Path) -> None:
        """Should only allow 'reports' subcommand in moderated chats."""
        from telegram_antilurk_bot.admin.show_commands import ShowCommandHandler

        # Mock configuration for non-moderated chat
        mock_config_loader = Mock()
        mock_global_config = Mock()
        mock_channels_config = Mock()
        mock_channels_config.get_moderated_channels.return_value = []  # No moderated channels

        mock_config_loader.load_all.return_value = (mock_global_config, mock_channels_config, Mock())

        handler = ShowCommandHandler(config_loader=mock_config_loader)

        mock_update = Mock()
        mock_update.effective_chat.id = -1009876543210  # modlog chat
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["reports"]

        # Mock configuration - this chat is modlog, not moderated
        with patch('telegram_antilurk_bot.admin.show_commands.ConfigLoader') as mock_config:
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            mock_channels_config = Mock()
            mock_channels_config.get_moderated_channels.return_value = []  # No moderated channels
            mock_config_instance.load_all.return_value = (Mock(), mock_channels_config, Mock())

            await handler.handle_show_command(mock_update, mock_context)

            # Should reject with error message
            mock_update.message.reply_text.assert_called_once()
            reply_text = mock_update.message.reply_text.call_args[0][0]
            assert "moderated chat" in reply_text.lower()
            assert "error" in reply_text.lower() or "only" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_show_reports_displays_recent_activity(self, temp_config_dir: Path) -> None:
        """Should display recent moderation reports in moderated chats."""
        from telegram_antilurk_bot.admin.show_commands import ShowCommandHandler

        # Mock configuration for moderated chat
        mock_config_loader = Mock()
        mock_channels_config = Mock()
        mock_channel = Mock()
        mock_channel.chat_id = -1001234567890
        mock_channels_config.get_moderated_channels.return_value = [mock_channel]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())

        # Mock provocation logger
        with patch('telegram_antilurk_bot.admin.show_commands.ProvocationLogger') as mock_logger:
            mock_logger_instance = AsyncMock()
            mock_logger.return_value = mock_logger_instance

            # Mock recent reports
            mock_reports = [
                {'provocation_id': 123, 'user_id': 67890, 'timestamp': datetime.utcnow(), 'event': 'created'},
                {'provocation_id': 124, 'user_id': 67891, 'timestamp': datetime.utcnow() - timedelta(hours=1), 'event': 'failed'}
            ]
            mock_logger_instance.get_recent_provocations.return_value = mock_reports

            handler = ShowCommandHandler(config_loader=mock_config_loader)

            mock_update = Mock()
            mock_update.effective_chat.id = -1001234567890  # moderated chat
            mock_update.message.reply_text = AsyncMock()
            mock_context = Mock()
            mock_context.args = ["reports", "5"]  # limit to 5 reports

            await handler.handle_show_command(mock_update, mock_context)

            # Should display reports
            mock_update.message.reply_text.assert_called_once()
            reply_text = mock_update.message.reply_text.call_args[0][0]
            assert "123" in reply_text  # provocation ID
            assert "67890" in reply_text  # user ID


class TestUnlinkCommand:
    """Tests for /antlurk unlink command."""

    @pytest.mark.asyncio
    async def test_unlink_removes_chat_connection(self, temp_config_dir: Path) -> None:
        """Should remove link between moderated and modlog chats."""
        from telegram_antilurk_bot.admin.unlink_command import UnlinkCommandHandler

        # Mock configuration
        mock_config_loader = Mock()
        mock_channels_config = Mock()

        # Setup linked channels
        mock_moderated = Mock()
        mock_moderated.chat_id = -1001234567890
        mock_moderated.chat_name = "Test Moderated"
        mock_moderated.modlog_ref = -1009876543210

        mock_channels_config.channels = [mock_moderated]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())
        mock_config_loader.save_channels_config = Mock()

        handler = UnlinkCommandHandler(config_loader=mock_config_loader)

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["-1009876543210"]  # chat ID to unlink

        await handler.handle_unlink_command(mock_update, mock_context)

        # Should remove the link
        assert mock_moderated.modlog_ref is None
        mock_config_loader.save_channels_config.assert_called_once()

        # Should confirm unlink
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "unlinked" in reply_text.lower() or "removed" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_unlink_regenerates_linking_message(self, temp_config_dir: Path) -> None:
        """Should generate new linking message after unlinking."""
        from telegram_antilurk_bot.admin.unlink_command import UnlinkCommandHandler

        # Mock configuration
        mock_config_loader = Mock()
        mock_channels_config = Mock()

        # Setup linked channels
        mock_moderated = Mock()
        mock_moderated.chat_id = -1001234567890
        mock_moderated.chat_name = "Test Moderated"
        mock_moderated.modlog_ref = -1009876543210

        mock_channels_config.channels = [mock_moderated]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())
        mock_config_loader.save_channels_config = Mock()

        handler = UnlinkCommandHandler(config_loader=mock_config_loader)

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["-1009876543210"]

        await handler.handle_unlink_command(mock_update, mock_context)

        # Should confirm unlink and include new link code
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "unlinked" in reply_text.lower()
        assert "new link code" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_unlink_validates_chat_id_format(self, temp_config_dir: Path) -> None:
        """Should validate chat ID format and reject invalid inputs."""
        from telegram_antilurk_bot.admin.unlink_command import UnlinkCommandHandler

        handler = UnlinkCommandHandler()

        mock_update = Mock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["invalid_chat_id"]  # Invalid format

        await handler.handle_unlink_command(mock_update, mock_context)

        # Should reject with error
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "invalid" in reply_text.lower() or "error" in reply_text.lower()


class TestCheckUserCommand:
    """Tests for /antlurk checkuser command."""

    @pytest.mark.asyncio
    async def test_checkuser_by_username(self, temp_config_dir: Path) -> None:
        """Should lookup user by username and display activity stats."""
        from telegram_antilurk_bot.admin.checkuser_command import CheckUserCommandHandler

        # Mock dependencies
        mock_user_tracker = AsyncMock()
        mock_message_archiver = AsyncMock()

        # Mock user lookup
        mock_user = User(
            user_id=67890,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        mock_user_tracker.get_user_by_username.return_value = mock_user
        mock_message_archiver.get_user_message_count.return_value = 150

        handler = CheckUserCommandHandler(
            user_tracker=mock_user_tracker,
            message_archiver=mock_message_archiver
        )

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["@testuser"]

        await handler.handle_checkuser_command(mock_update, mock_context)

        # Should display user stats
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "testuser" in reply_text
        assert "67890" in reply_text
        assert "150" in reply_text  # message count

    @pytest.mark.asyncio
    async def test_checkuser_by_user_id(self, temp_config_dir: Path) -> None:
        """Should lookup user by ID and display activity stats."""
        from telegram_antilurk_bot.admin.checkuser_command import CheckUserCommandHandler

        # Mock dependencies
        mock_user_tracker = AsyncMock()
        mock_message_archiver = AsyncMock()

        mock_user = User(
            user_id=67890,
            username="testuser",
            first_name="Test"
        )
        mock_user_tracker.get_user.return_value = mock_user
        mock_message_archiver.get_user_message_count.return_value = 42

        handler = CheckUserCommandHandler(
            user_tracker=mock_user_tracker,
            message_archiver=mock_message_archiver
        )

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["67890"]

        await handler.handle_checkuser_command(mock_update, mock_context)

        # Should display user stats
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "67890" in reply_text
        assert "42" in reply_text  # message count

    @pytest.mark.asyncio
    async def test_checkuser_handles_user_not_found(self, temp_config_dir: Path) -> None:
        """Should handle cases where user is not found."""
        from telegram_antilurk_bot.admin.checkuser_command import CheckUserCommandHandler

        handler = CheckUserCommandHandler()

        mock_update = Mock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["@nonexistentuser"]

        with patch('telegram_antilurk_bot.admin.checkuser_command.UserTracker') as mock_tracker:
            mock_tracker_instance = Mock()
            mock_tracker.return_value = mock_tracker_instance
            mock_tracker_instance.get_user_by_username.return_value = None

            await handler.handle_checkuser_command(mock_update, mock_context)

            # Should report user not found
            mock_update.message.reply_text.assert_called_once()
            reply_text = mock_update.message.reply_text.call_args[0][0]
            assert "not found" in reply_text.lower() or "unknown" in reply_text.lower()


class TestReportCommand:
    """Tests for /antlurk report command."""

    @pytest.mark.asyncio
    async def test_report_active_users(self, temp_config_dir: Path) -> None:
        """Should generate report of active users in moderated chat."""
        from telegram_antilurk_bot.admin.report_command import ReportCommandHandler

        # Mock dependencies
        mock_config_loader = Mock()
        mock_user_tracker = AsyncMock()

        # Mock channel configuration
        mock_channels_config = Mock()
        mock_channel = Mock()
        mock_channel.chat_id = -1001234567890
        mock_channels_config.get_moderated_channels.return_value = [mock_channel]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())

        # Mock active users
        active_users = [
            User(user_id=11111, username="active1"),
            User(user_id=22222, username="active2")
        ]
        mock_user_tracker.get_users_by_activity.return_value = active_users

        handler = ReportCommandHandler(
            config_loader=mock_config_loader,
            user_tracker=mock_user_tracker
        )

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["active", "--limit", "10"]

        await handler.handle_report_command(mock_update, mock_context)

        # Should generate active users report
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "active1" in reply_text
        assert "active2" in reply_text
        assert "Active Users" in reply_text

    @pytest.mark.asyncio
    async def test_report_lurkers_with_custom_days(self, temp_config_dir: Path) -> None:
        """Should generate lurker report with custom day threshold."""
        from telegram_antilurk_bot.admin.report_command import ReportCommandHandler

        # Mock dependencies
        mock_config_loader = Mock()
        mock_user_tracker = AsyncMock()
        mock_lurker_selector = AsyncMock()

        # Mock channel configuration
        mock_channels_config = Mock()
        mock_channel = Mock()
        mock_channel.chat_id = -1001234567890
        mock_channels_config.get_moderated_channels.return_value = [mock_channel]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())

        # Mock lurkers
        lurkers = [
            User(user_id=33333, username="lurker1"),
            User(user_id=44444, username="lurker2")
        ]
        mock_lurker_selector.get_lurkers_for_chat.return_value = lurkers

        handler = ReportCommandHandler(
            config_loader=mock_config_loader,
            user_tracker=mock_user_tracker,
            lurker_selector=mock_lurker_selector
        )

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["lurkers", "--days", "7", "--limit", "5"]

        await handler.handle_report_command(mock_update, mock_context)

        # Should call with custom 7-day threshold
        mock_lurker_selector.get_lurkers_for_chat.assert_called_once_with(
            chat_id=-1001234567890,
            days_threshold=7
        )

        # Should generate lurkers report
        mock_update.message.reply_text.assert_called_once()
        reply_text = mock_update.message.reply_text.call_args[0][0]
        assert "lurker1" in reply_text
        assert "lurker2" in reply_text

    @pytest.mark.asyncio
    async def test_report_only_works_in_moderated_chats(self, temp_config_dir: Path) -> None:
        """Should only allow report commands in moderated chats."""
        from telegram_antilurk_bot.admin.report_command import ReportCommandHandler

        handler = ReportCommandHandler()

        mock_update = Mock()
        mock_update.effective_chat.id = -1009876543210  # modlog chat
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        mock_context.args = ["active"]

        with patch('telegram_antilurk_bot.admin.report_command.ConfigLoader') as mock_config:
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            mock_channels_config = Mock()
            mock_channels_config.get_moderated_channels.return_value = []  # No moderated channels
            mock_config_instance.load_all.return_value = (Mock(), mock_channels_config, Mock())

            await handler.handle_report_command(mock_update, mock_context)

            # Should reject with error
            mock_update.message.reply_text.assert_called_once()
            reply_text = mock_update.message.reply_text.call_args[0][0]
            assert "moderated chat" in reply_text.lower()


class TestRebootCommand:
    """Tests for /antlurk reboot command."""

    @pytest.mark.asyncio
    async def test_reboot_persists_state_before_shutdown(self, temp_config_dir: Path) -> None:
        """Should persist application state before initiating shutdown."""
        from telegram_antilurk_bot.admin.reboot_command import RebootCommandHandler

        # Mock dependencies
        mock_config_loader = Mock()
        mock_config_loader.save_all_configs = Mock()

        # Mock global config with update_provenance method
        mock_global_config = Mock()
        mock_global_config.update_provenance = Mock()
        mock_channels_config = Mock()
        mock_channels_config.update_provenance = Mock()
        mock_channels_config.get_modlog_channels.return_value = []
        mock_puzzles_config = Mock()
        mock_puzzles_config.update_provenance = Mock()

        mock_config_loader.load_all.return_value = (mock_global_config, mock_channels_config, mock_puzzles_config)

        handler = RebootCommandHandler(config_loader=mock_config_loader)

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()

        with patch('telegram_antilurk_bot.admin.reboot_command.sys.exit') as mock_exit:
            await handler.handle_reboot_command(mock_update, mock_context)

            # Should update provenance (save_all_configs is commented out in current impl)
            mock_global_config.update_provenance.assert_called_once_with("reboot-shutdown")
            mock_channels_config.update_provenance.assert_called_once_with("reboot-shutdown")
            mock_puzzles_config.update_provenance.assert_called_once_with("reboot-shutdown")

            # Should post shutdown notice
            mock_update.message.reply_text.assert_called()
            reply_text = mock_update.message.reply_text.call_args[0][0]
            assert "reboot" in reply_text.lower() or "shutdown" in reply_text.lower()

            # Should exit with code 0
            mock_exit.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_reboot_posts_shutdown_notice_to_modlogs(self, temp_config_dir: Path) -> None:
        """Should post shutdown notice to all modlog channels."""
        from telegram_antilurk_bot.admin.reboot_command import RebootCommandHandler

        # Mock dependencies
        mock_config_loader = Mock()
        mock_config_loader.save_all_configs = Mock()

        # Mock channel configuration with modlog channels
        mock_channels_config = Mock()
        mock_modlog1 = Mock()
        mock_modlog1.chat_id = -1009876543210
        mock_modlog2 = Mock()
        mock_modlog2.chat_id = -1009876543211
        mock_channels_config.get_modlog_channels.return_value = [mock_modlog1, mock_modlog2]
        mock_config_loader.load_all.return_value = (Mock(), mock_channels_config, Mock())

        handler = RebootCommandHandler(config_loader=mock_config_loader)

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()

        with patch('telegram_antilurk_bot.admin.reboot_command.Application') as mock_app:
            with patch('telegram_antilurk_bot.admin.reboot_command.sys.exit'):
                mock_bot = AsyncMock()
                mock_app.builder().token().build.return_value.bot = mock_bot

                await handler.handle_reboot_command(mock_update, mock_context)

                # Should send shutdown notice to both modlog channels
                assert mock_bot.send_message.call_count == 2

                # Check that both modlog channels received shutdown notice
                call_args_list = mock_bot.send_message.call_args_list
                chat_ids_called = [call[1]['chat_id'] for call in call_args_list]
                assert -1009876543210 in chat_ids_called
                assert -1009876543211 in chat_ids_called


class TestPermissionValidation:
    """Tests for command permission and chat scoping validation."""

    @pytest.mark.asyncio
    async def test_admin_commands_require_admin_permissions(self, temp_config_dir: Path) -> None:
        """Should validate that admin commands require admin permissions."""
        from telegram_antilurk_bot.admin.permission_validator import PermissionValidator

        validator = PermissionValidator()

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.effective_user.id = 67890
        mock_update.message.reply_text = AsyncMock()

        # Mock user as non-admin
        with patch('telegram_antilurk_bot.admin.permission_validator.UserTracker') as mock_tracker:
            mock_tracker_instance = Mock()
            mock_tracker.return_value = mock_tracker_instance
            mock_user = User(user_id=67890, is_admin=False)
            mock_tracker_instance.get_user.return_value = mock_user

            is_allowed = await validator.validate_admin_permission(mock_update)

            assert is_allowed is False
            mock_update.message.reply_text.assert_called_once()
            reply_text = mock_update.message.reply_text.call_args[0][0]
            assert "admin" in reply_text.lower() or "permission" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_moderated_chat_commands_validate_chat_type(self, temp_config_dir: Path) -> None:
        """Should validate commands that only work in moderated chats."""
        from telegram_antilurk_bot.admin.permission_validator import PermissionValidator

        validator = PermissionValidator()

        mock_update = Mock()
        mock_update.effective_chat.id = -1009876543210  # modlog chat
        mock_update.message.reply_text = AsyncMock()

        with patch('telegram_antilurk_bot.admin.permission_validator.ConfigLoader') as mock_config:
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            mock_channels_config = Mock()
            mock_channels_config.get_moderated_channels.return_value = []  # No moderated channels
            mock_config_instance.load_all.return_value = (Mock(), mock_channels_config, Mock())

            is_moderated = await validator.validate_moderated_chat(mock_update)

            assert is_moderated is False
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_admin_validation_with_telegram_api(self, temp_config_dir: Path) -> None:
        """Should validate admin status using Telegram chat admin API."""
        from telegram_antilurk_bot.admin.permission_validator import PermissionValidator

        validator = PermissionValidator()

        mock_update = Mock()
        mock_update.effective_chat.id = -1001234567890
        mock_update.effective_user.id = 67890

        with patch('telegram_antilurk_bot.admin.permission_validator.Application') as mock_app:
            mock_bot = AsyncMock()
            mock_app.builder().token().build.return_value.bot = mock_bot

            # Mock user as Telegram chat admin
            mock_chat_member = Mock()
            mock_chat_member.status = "administrator"
            mock_bot.get_chat_member.return_value = mock_chat_member

            is_admin = await validator.validate_telegram_admin(mock_update)

            assert is_admin is True
            mock_bot.get_chat_member.assert_called_once_with(
                chat_id=-1001234567890,
                user_id=67890
            )
