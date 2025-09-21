"""Unit tests for configuration schemas - written FIRST in TDD style."""


import pytest
from pydantic import ValidationError


class TestGlobalConfigSchema:
    """Tests for GlobalConfig schema."""

    def test_global_config_with_defaults(self) -> None:
        """GlobalConfig should have sensible defaults."""
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        config = GlobalConfig()

        assert config.lurk_threshold_days == 14
        assert config.provocation_interval_hours == 48
        assert config.audit_cadence_minutes == 15
        assert config.rate_limit_per_hour == 2
        assert config.rate_limit_per_day == 15
        assert config.enable_nats is False
        assert config.enable_announcements is False

    def test_global_config_with_custom_values(self) -> None:
        """GlobalConfig should accept custom values within valid ranges."""
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        config = GlobalConfig(
            lurk_threshold_days=7,
            provocation_interval_hours=24,
            audit_cadence_minutes=30,
            rate_limit_per_hour=5,
            rate_limit_per_day=50
        )

        assert config.lurk_threshold_days == 7
        assert config.provocation_interval_hours == 24
        assert config.audit_cadence_minutes == 30
        assert config.rate_limit_per_hour == 5
        assert config.rate_limit_per_day == 50

    def test_global_config_validation_errors(self) -> None:
        """GlobalConfig should reject invalid values."""
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        with pytest.raises(ValidationError) as exc_info:
            GlobalConfig(lurk_threshold_days=0)  # Too low
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            GlobalConfig(lurk_threshold_days=400)  # Too high
        assert "less than or equal to 365" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            GlobalConfig(audit_cadence_minutes=3)  # Too low
        assert "greater than or equal to 5" in str(exc_info.value)

    def test_global_config_checksum_computation(self) -> None:
        """GlobalConfig should compute consistent checksums."""
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        config1 = GlobalConfig(lurk_threshold_days=7)
        config2 = GlobalConfig(lurk_threshold_days=7)
        config3 = GlobalConfig(lurk_threshold_days=14)

        # Same config should produce same checksum
        assert config1.compute_checksum() == config2.compute_checksum()

        # Different config should produce different checksum
        assert config1.compute_checksum() != config3.compute_checksum()

        # Checksum should be a valid hex string
        checksum = config1.compute_checksum()
        assert len(checksum) == 64  # SHA256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_global_config_provenance_update(self) -> None:
        """GlobalConfig should track provenance correctly."""
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        config = GlobalConfig()
        initial_time = config.provenance.updated_at
        initial_checksum = config.provenance.checksum

        # Update provenance
        config.update_provenance("test-user")

        assert config.provenance.updated_by == "test-user"
        assert config.provenance.updated_at > initial_time
        assert config.provenance.checksum is not None
        assert config.provenance.checksum != initial_checksum


class TestPuzzleSchema:
    """Tests for Puzzle schema."""

    def test_valid_puzzle_creation(self) -> None:
        """Puzzle should accept valid configuration."""
        from telegram_antilurk_bot.config.schemas import Puzzle

        puzzle = Puzzle(
            id="test_001",
            type="arithmetic",
            question="What is 2 + 2?",
            choices=["4", "3", "5", "6"]  # First choice is correct
        )

        assert puzzle.id == "test_001"
        assert puzzle.type == "arithmetic"
        assert puzzle.question == "What is 2 + 2?"
        assert len(puzzle.choices) == 4
        assert puzzle.get_correct_answer() == "4"
        assert puzzle.get_wrong_answers() == ["3", "5", "6"]

    def test_puzzle_type_validation(self) -> None:
        """Puzzle should only accept valid types."""
        from telegram_antilurk_bot.config.schemas import Puzzle

        choices = ["A", "B", "C"]  # First choice is correct

        # Valid types
        puzzle1 = Puzzle(id="p1", type="arithmetic", question="Q?", choices=choices)
        assert puzzle1.type == "arithmetic"

        puzzle2 = Puzzle(id="p2", type="common_sense", question="Q?", choices=choices)
        assert puzzle2.type == "common_sense"

        # Invalid type
        with pytest.raises(ValidationError) as exc_info:
            Puzzle(id="p3", type="invalid_type", question="Q?", choices=choices)
        assert "pattern" in str(exc_info.value).lower()

    def test_puzzle_choices_validation(self) -> None:
        """Puzzle should validate choice requirements."""
        from telegram_antilurk_bot.config.schemas import Puzzle

        # Too few choices
        with pytest.raises(ValidationError) as exc_info:
            Puzzle(
                id="p1",
                type="arithmetic",
                question="Q?",
                choices=["A", "B"]  # Only 2 choices, need at least 3
            )
        assert "at least 3" in str(exc_info.value).lower()

        # Too many choices
        with pytest.raises(ValidationError) as exc_info:
            Puzzle(
                id="p2",
                type="arithmetic",
                question="Q?",
                choices=["A", "B", "C", "D", "E"]  # 5 choices, max is 4
            )
        assert "at most 4" in str(exc_info.value).lower()

        # Valid choices
        puzzle = Puzzle(
            id="p3",
            type="arithmetic",
            question="Q?",
            choices=["A", "B", "C"]  # Minimum 3 choices
        )
        assert len(puzzle.choices) == 3
        assert puzzle.get_correct_answer() == "A"



class TestChannelSchema:
    """Tests for Channel configuration schema."""

    def test_channel_entry_creation(self) -> None:
        """ChannelEntry should store channel configuration."""
        from telegram_antilurk_bot.config.schemas import ChannelEntry

        channel = ChannelEntry(
            chat_id=-1001234567890,
            chat_name="Test Channel",
            mode="moderated"
        )

        assert channel.chat_id == -1001234567890
        assert channel.chat_name == "Test Channel"
        assert channel.mode == "moderated"
        assert channel.modlog_ref is None
        assert channel.overrides is None

    def test_channel_mode_validation(self) -> None:
        """ChannelEntry should only accept valid modes."""
        from telegram_antilurk_bot.config.schemas import ChannelEntry

        # Valid modes
        channel1 = ChannelEntry(chat_id=1, chat_name="C1", mode="moderated")
        assert channel1.mode == "moderated"

        channel2 = ChannelEntry(chat_id=2, chat_name="C2", mode="modlog")
        assert channel2.mode == "modlog"

        # Invalid mode
        with pytest.raises(ValidationError) as exc_info:
            ChannelEntry(chat_id=3, chat_name="C3", mode="invalid")
        assert "pattern" in str(exc_info.value).lower()

    def test_channel_overrides(self) -> None:
        """ChannelEntry should accept per-channel overrides."""
        from telegram_antilurk_bot.config.schemas import ChannelEntry, ChannelOverride

        override = ChannelOverride(
            lurk_threshold_days=7,
            rate_limit_per_hour=3
        )

        channel = ChannelEntry(
            chat_id=-1001234567890,
            chat_name="Test Channel",
            mode="moderated",
            overrides=override
        )

        assert channel.overrides is not None
        assert channel.overrides.lurk_threshold_days == 7
        assert channel.overrides.rate_limit_per_hour == 3
        assert channel.overrides.audit_cadence_minutes is None  # Not overridden

    def test_channels_config_methods(self) -> None:
        """ChannelsConfig should provide helper methods."""
        from telegram_antilurk_bot.config.schemas import ChannelEntry, ChannelsConfig

        config = ChannelsConfig(channels=[
            ChannelEntry(chat_id=1, chat_name="Mod1", mode="moderated", modlog_ref=3),
            ChannelEntry(chat_id=2, chat_name="Mod2", mode="moderated", modlog_ref=3),
            ChannelEntry(chat_id=3, chat_name="Log1", mode="modlog"),
            ChannelEntry(chat_id=4, chat_name="Log2", mode="modlog"),
        ])

        # Get moderated channels
        moderated = config.get_moderated_channels()
        assert len(moderated) == 2
        assert all(ch.mode == "moderated" for ch in moderated)

        # Get modlog channels
        modlogs = config.get_modlog_channels()
        assert len(modlogs) == 2
        assert all(ch.mode == "modlog" for ch in modlogs)

        # Get linked modlog
        linked = config.get_linked_modlog(1)
        assert linked is not None
        assert linked.chat_id == 3

        # No link found
        no_link = config.get_linked_modlog(4)
        assert no_link is None
