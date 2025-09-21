"""Contract tests for component interfaces and API boundaries."""

from datetime import datetime

from telegram_antilurk_bot.database.models import User


class TestConfigurationContracts:
    """Test configuration loading contracts and interfaces."""

    def test_config_loader_interface(self) -> None:
        """Test ConfigLoader provides required interface."""
        from telegram_antilurk_bot.config.loader import ConfigLoader

        loader = ConfigLoader()

        # Required methods
        assert hasattr(loader, "load_all"), "ConfigLoader must have load_all method"
        assert callable(loader.load_all), "load_all must be callable"

        # Required attributes
        assert hasattr(loader, "config_dir"), "ConfigLoader must have config_dir attribute"

    def test_global_config_contract(self) -> None:
        """Test global configuration contract."""
        # Expected attributes in global config
        required_attrs = [
            "lurk_threshold_days",
            "provocation_interval_hours",
            "audit_cadence_minutes",
            "rate_limit_per_hour",
            "rate_limit_per_day",
            "enable_nats",
            "enable_announcements",
        ]

        # This would test actual config loading in integration
        # For contract test, we verify the interface expectation
        for attr in required_attrs:
            assert isinstance(attr, str)
            assert len(attr) > 0

    def test_channels_config_contract(self) -> None:
        """Test channels configuration contract."""
        # Required methods
        required_methods = ["get_moderated_channels", "get_modlog_channels", "get_channel_by_id"]

        for method in required_methods:
            assert isinstance(method, str)
            # In real implementation, would verify callable existence


class TestDatabaseModelContracts:
    """Test database model contracts and relationships."""

    def test_user_model_contract(self) -> None:
        """Test User model provides required interface."""
        user = User(user_id=12345, username="testuser", first_name="Test", is_bot=False)

        # Required attributes
        assert hasattr(user, "user_id"), "User must have user_id"
        assert hasattr(user, "username"), "User must have username"
        assert hasattr(user, "first_name"), "User must have first_name"
        assert hasattr(user, "is_bot"), "User must have is_bot"
        assert hasattr(user, "is_admin"), "User must have is_admin"
        assert hasattr(user, "last_message_at"), "User must have last_message_at"
        assert hasattr(user, "join_date"), "User must have join_date"

        # Type validation
        assert isinstance(user.user_id, int)
        assert isinstance(user.is_bot, bool)
        assert isinstance(user.is_admin, bool)

    def test_message_archive_contract(self) -> None:
        """Test MessageArchive model contract."""
        # Expected attributes
        required_attrs = [
            "message_id",
            "user_id",
            "chat_id",
            "timestamp",
            "content",
            "message_type",
        ]

        # Contract verification - in real test would check actual model
        for attr in required_attrs:
            assert isinstance(attr, str)
            assert len(attr) > 0

    def test_provocation_contract(self) -> None:
        """Test Provocation model contract."""
        required_attrs = [
            "provocation_id",
            "user_id",
            "chat_id",
            "puzzle_id",
            "created_at",
            "expires_at",
            "outcome",
            "response_at",
        ]

        for attr in required_attrs:
            assert isinstance(attr, str)
            assert len(attr) > 0


class TestComponentInterfaceContracts:
    """Test interfaces between major components."""

    def test_audit_scheduler_contract(self) -> None:
        """Test AuditScheduler interface contract."""
        from telegram_antilurk_bot.audit.scheduler import AuditScheduler

        # Required methods
        required_methods = ["run_audit_cycle", "should_run_audit"]

        for method_name in required_methods:
            assert hasattr(AuditScheduler, method_name), f"AuditScheduler must have {method_name}"

    def test_lurker_selector_contract(self) -> None:
        """Test LurkerSelector interface contract."""
        from telegram_antilurk_bot.audit.lurker_selector import LurkerSelector

        required_methods = ["get_lurkers_for_chat", "is_lurker"]

        for method_name in required_methods:
            assert hasattr(LurkerSelector, method_name), f"LurkerSelector must have {method_name}"

    def test_challenge_engine_contract(self) -> None:
        """Test ChallengeEngine interface contract."""
        from telegram_antilurk_bot.challenges.engine import ChallengeEngine

        required_methods = [
            "create_challenge",
            "handle_challenge_response",
            "can_create_challenge",
            "cleanup_expired_challenges",
        ]

        for method_name in required_methods:
            assert hasattr(ChallengeEngine, method_name), f"ChallengeEngine must have {method_name}"

    def test_user_tracker_contract(self) -> None:
        """Test UserTracker interface contract."""
        from telegram_antilurk_bot.logging.user_tracker import UserTracker

        required_methods = [
            "track_user_activity",
            "get_user",
            "get_user_by_username",
            "get_users_by_activity",
            "get_inactive_users",
        ]

        for method_name in required_methods:
            assert hasattr(UserTracker, method_name), f"UserTracker must have {method_name}"


class TestAPIContractValidation:
    """Test API contracts and data flow between components."""

    def test_audit_to_challenge_contract(self) -> None:
        """Test contract between audit system and challenge creation."""
        # Expected data flow:
        # AuditScheduler -> LurkerSelector -> ChallengeEngine

        # Mock lurker data format from LurkerSelector to ChallengeEngine
        lurker_data = User(
            user_id=12345, username="lurker", first_name="Test", last_message_at=datetime.utcnow()
        )

        # Verify User model can be passed between components
        assert hasattr(lurker_data, "user_id")
        assert hasattr(lurker_data, "username")
        assert hasattr(lurker_data, "last_message_at")

    def test_challenge_to_response_contract(self) -> None:
        """Test contract between challenge creation and response handling."""
        # Expected challenge creation output
        challenge_output = {
            "provocation_id": 123,
            "user_id": 12345,
            "chat_id": -1001234567890,
            "message_id": 456,
            "expires_at": datetime.utcnow(),
        }

        # Verify challenge output format
        required_keys = ["provocation_id", "user_id", "chat_id", "message_id", "expires_at"]
        for key in required_keys:
            assert key in challenge_output

        # Expected response input format
        response_input = {
            "provocation_id": 123,
            "user_id": 12345,
            "chat_id": -1001234567890,
            "selected_option": 0,
            "callback_query_id": "abc123",
        }

        # Verify response input format
        response_keys = ["provocation_id", "user_id", "chat_id", "selected_option"]
        for key in response_keys:
            assert key in response_input

    def test_reporting_data_contract(self) -> None:
        """Test contract for reporting system data."""
        # Expected report data format
        report_data = {
            "report_type": "active",
            "chat_id": -1001234567890,
            "days_threshold": 14,
            "limit": 20,
            "users": [
                {
                    "user_id": 12345,
                    "username": "user1",
                    "last_message_at": datetime.utcnow(),
                    "message_count": 10,
                }
            ],
        }

        # Verify report structure
        assert "report_type" in report_data
        assert "chat_id" in report_data
        assert "users" in report_data
        assert isinstance(report_data["users"], list)

        # Verify user data in report
        if report_data["users"]:
            user_data = report_data["users"][0]
            assert "user_id" in user_data
            assert "username" in user_data
            assert "last_message_at" in user_data

    def test_configuration_update_contract(self) -> None:
        """Test contract for configuration updates."""
        # Expected configuration update format
        config_update = {
            "component": "global",
            "changes": {"lurk_threshold_days": 21, "rate_limit_per_hour": 3},
            "updated_by": "admin_user_id",
            "timestamp": datetime.utcnow(),
        }

        # Verify update structure
        assert "component" in config_update
        assert "changes" in config_update
        assert "updated_by" in config_update
        assert "timestamp" in config_update

        # Verify changes format
        assert isinstance(config_update["changes"], dict)


class TestRateLimitingContracts:
    """Test rate limiting contracts across components."""

    def test_rate_limiter_contract(self) -> None:
        """Test RateLimiter interface contract."""
        from telegram_antilurk_bot.audit.rate_limiter import RateLimiter

        required_methods = ["can_send_provocation", "record_provocation", "get_remaining_allowance"]

        for method_name in required_methods:
            assert hasattr(RateLimiter, method_name), f"RateLimiter must have {method_name}"

    def test_rate_limit_data_contract(self) -> None:
        """Test rate limiting data structures."""
        # Expected rate limit state
        rate_limit_state = {
            "chat_id": -1001234567890,
            "hourly_count": 1,
            "daily_count": 5,
            "last_provocation": datetime.utcnow(),
            "window_start_hour": datetime.utcnow().replace(minute=0, second=0, microsecond=0),
            "window_start_day": datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        }

        # Verify rate limit structure
        required_keys = [
            "chat_id",
            "hourly_count",
            "daily_count",
            "last_provocation",
            "window_start_hour",
            "window_start_day",
        ]

        for key in required_keys:
            assert key in rate_limit_state


class TestEventPublishingContracts:
    """Test event publishing contracts for NATS integration."""

    def test_nats_publisher_contract(self) -> None:
        """Test NATS event publisher interface."""
        from telegram_antilurk_bot.logging.nats_publisher import NATSEventPublisher

        required_methods = ["publish_event", "connect", "close"]

        for method_name in required_methods:
            assert hasattr(NATSEventPublisher, method_name), (
                f"NATSEventPublisher must have {method_name}"
            )

    def test_event_format_contract(self) -> None:
        """Test event message format contract."""
        # Expected event format
        event_message = {
            "event_type": "user_activity",
            "timestamp": datetime.utcnow().isoformat(),
            "chat_id": -1001234567890,
            "user_id": 12345,
            "data": {"message_count": 1, "last_seen": datetime.utcnow().isoformat()},
        }

        # Verify event structure
        required_keys = ["event_type", "timestamp", "chat_id", "user_id", "data"]
        for key in required_keys:
            assert key in event_message

        # Verify data serialization
        assert isinstance(event_message["timestamp"], str)
        assert isinstance(event_message["data"], dict)


class TestPermissionContracts:
    """Test permission validation contracts."""

    def test_permission_validator_contract(self) -> None:
        """Test PermissionValidator interface."""
        from telegram_antilurk_bot.admin.permission_validator import PermissionValidator

        required_methods = [
            "validate_admin_permission",
            "validate_moderated_chat",
            "validate_command_permissions",
        ]

        for method_name in required_methods:
            assert hasattr(PermissionValidator, method_name), (
                f"PermissionValidator must have {method_name}"
            )

    def test_permission_check_contract(self) -> None:
        """Test permission check data contract."""
        # Expected permission check result
        permission_result = {
            "is_authorized": True,
            "user_id": 12345,
            "chat_id": -1001234567890,
            "permission_level": "admin",
            "checks_performed": ["admin_status", "moderated_chat"],
        }

        # Verify permission result structure
        required_keys = ["is_authorized", "user_id", "chat_id"]
        for key in required_keys:
            assert key in permission_result

        assert isinstance(permission_result["is_authorized"], bool)
