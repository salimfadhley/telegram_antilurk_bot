"""Unit tests for configuration loader - TDD style."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_config_loader_initialization(self, temp_config_dir: Path) -> None:
        """ConfigLoader should initialize with config directory."""
        from telegram_antilurk_bot.config.loader import ConfigLoader

        loader = ConfigLoader(config_dir=temp_config_dir)
        assert loader.config_dir == temp_config_dir
        assert loader.config_path == temp_config_dir / 'config.yaml'
        assert loader.channels_path == temp_config_dir / 'channels.yaml'
        assert loader.puzzles_path == temp_config_dir / 'puzzles.yaml'

    def test_config_loader_uses_environment_variable(self) -> None:
        """ConfigLoader should use CONFIG_DIR from environment if not specified."""
        from telegram_antilurk_bot.config.loader import ConfigLoader

        with patch.dict('os.environ', {'CONFIG_DIR': '/custom/config'}):
            loader = ConfigLoader()
            assert str(loader.config_dir) == '/custom/config'

    def test_config_loader_creates_directory_if_missing(self, temp_config_dir: Path) -> None:
        """ConfigLoader should create config directory if it doesn't exist."""
        from telegram_antilurk_bot.config.loader import ConfigLoader

        new_dir = temp_config_dir / 'new_subdir'
        assert not new_dir.exists()

        ConfigLoader(config_dir=new_dir)
        assert new_dir.exists()

    def test_load_all_creates_default_files_if_missing(self, temp_config_dir: Path) -> None:
        """ConfigLoader should create default config files if they don't exist."""
        from telegram_antilurk_bot.config.loader import ConfigLoader

        loader = ConfigLoader(config_dir=temp_config_dir)

        # Files shouldn't exist initially
        assert not loader.config_path.exists()
        assert not loader.channels_path.exists()
        assert not loader.puzzles_path.exists()

        # Load all configs
        global_config, channels_config, puzzles_config = loader.load_all()

        # Files should now exist
        assert loader.config_path.exists()
        assert loader.channels_path.exists()
        assert loader.puzzles_path.exists()

        # Configs should have defaults
        assert global_config.lurk_threshold_days == 14
        assert len(channels_config.channels) == 0
        assert len(puzzles_config.puzzles) >= 50  # Should have default puzzles

    def test_load_global_config_validates_checksum(self, temp_config_dir: Path) -> None:
        """ConfigLoader should validate checksum and detect manual edits."""
        from telegram_antilurk_bot.config.loader import ConfigLoader
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        loader = ConfigLoader(config_dir=temp_config_dir)

        # Create a config with valid checksum
        config = GlobalConfig(lurk_threshold_days=7)
        config.update_provenance("test-init")

        # Save it manually
        config_dict = config.model_dump(mode='json')
        with open(loader.config_path, 'w') as f:
            yaml.dump(config_dict, f)

        # Now manually edit the file (simulate manual edit)
        with open(loader.config_path) as f:
            data = yaml.safe_load(f)
        data['lurk_threshold_days'] = 10  # Change a value
        with open(loader.config_path, 'w') as f:
            yaml.dump(data, f)

        # Load should detect checksum mismatch
        with patch('telegram_antilurk_bot.config.loader.logger') as mock_logger:
            loaded_config = loader._load_global_config()

            # Should log a warning about checksum mismatch
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args[0]
            assert "checksum mismatch" in call_args[0].lower()

        # Config should be adopted with new checksum
        assert loaded_config.lurk_threshold_days == 10
        assert loaded_config.provenance.checksum is not None

    def test_load_invalid_config_exits(self, temp_config_dir: Path) -> None:
        """ConfigLoader should exit with clear error on invalid config."""
        from telegram_antilurk_bot.config.loader import ConfigLoader

        loader = ConfigLoader(config_dir=temp_config_dir)

        # Write invalid config
        with open(loader.config_path, 'w') as f:
            yaml.dump({'lurk_threshold_days': -1}, f)  # Invalid value

        # Should exit with error
        with pytest.raises(SystemExit) as exc_info:
            loader._load_global_config()
        assert exc_info.value.code == 1

    def test_save_config_detects_manual_edits(self, temp_config_dir: Path) -> None:
        """Save should detect and warn about manual edits before overwriting."""
        from telegram_antilurk_bot.config.loader import ConfigLoader
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        loader = ConfigLoader(config_dir=temp_config_dir)

        # Create initial config
        config1 = GlobalConfig(lurk_threshold_days=7)
        old_checksum, _ = loader.save_global_config(config1, "initial")
        assert old_checksum is None  # No previous config

        # Manually edit the file
        with open(loader.config_path) as f:
            data = yaml.safe_load(f)
        data['lurk_threshold_days'] = 10
        with open(loader.config_path, 'w') as f:
            yaml.dump(data, f)

        # Save new config should detect manual edit
        config2 = GlobalConfig(lurk_threshold_days=14)
        with patch('telegram_antilurk_bot.config.loader.logger') as mock_logger:
            old_checksum, new_checksum = loader.save_global_config(config2, "update")

            # Should have detected manual edit
            assert old_checksum is not None
            assert new_checksum != old_checksum

            # Should log warning
            mock_logger.warning.assert_called()

    def test_default_puzzles_generation(self) -> None:
        """Should generate a good set of default puzzles."""
        from telegram_antilurk_bot.config.defaults import get_default_puzzles

        puzzles = get_default_puzzles()

        # Should have at least 50 puzzles
        assert len(puzzles) >= 50

        # Should have both types
        arithmetic_count = sum(1 for p in puzzles if p.type == "arithmetic")
        common_sense_count = sum(1 for p in puzzles if p.type == "common_sense")
        assert arithmetic_count >= 20
        assert common_sense_count >= 20

        # Each puzzle should be valid
        for puzzle in puzzles:
            assert puzzle.id
            assert puzzle.question
            assert 3 <= len(puzzle.choices) <= 4
            # First choice is always correct in new format
            assert puzzle.get_correct_answer() == puzzle.choices[0]
            assert len(puzzle.get_wrong_answers()) == len(puzzle.choices) - 1

    def test_config_persistence_format(self, temp_config_dir: Path) -> None:
        """Saved configs should be properly formatted YAML."""
        from telegram_antilurk_bot.config.loader import ConfigLoader
        from telegram_antilurk_bot.config.schemas import GlobalConfig

        loader = ConfigLoader(config_dir=temp_config_dir)

        config = GlobalConfig(
            lurk_threshold_days=7,
            provocation_interval_hours=24,
            enable_nats=True
        )

        loader.save_global_config(config, "test")

        # Read back as raw YAML
        with open(loader.config_path) as f:
            data = yaml.safe_load(f)

        # Check structure
        assert data['lurk_threshold_days'] == 7
        assert data['provocation_interval_hours'] == 24
        assert data['enable_nats'] is True
        assert 'provenance' in data
        assert 'updated_at' in data['provenance']
        assert 'updated_by' in data['provenance']
        assert 'checksum' in data['provenance']
