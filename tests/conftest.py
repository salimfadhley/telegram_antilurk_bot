"""Shared pytest fixtures and configuration."""

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from faker import Faker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set test environment variables
os.environ["TELEGRAM_TOKEN"] = "test_token_123456789:ABCdefGhIJKlmNoPQRstuVwxyZ"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_antilurk"


@pytest.fixture
def fake() -> Faker:
    """Provide Faker instance for test data generation."""
    return Faker()


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_telegram_bot() -> AsyncMock:
    """Mock Telegram bot instance."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=Mock(message_id=12345))
    bot.delete_message = AsyncMock(return_value=True)
    return bot


@pytest.fixture
def sample_config_data() -> dict[str, Any]:
    """Sample configuration data for testing."""
    return {
        "global_config": {
            "lurk_threshold_days": 14,
            "provocation_interval_hours": 48,
            "audit_cadence_minutes": 15,
            "rate_limit_per_hour": 2,
            "rate_limit_per_day": 15,
            "enable_nats": False,
            "enable_announcements": False,
        },
        "channels": [
            {
                "chat_id": -1001234567890,
                "chat_name": "Test Channel",
                "mode": "moderated",
                "modlog_ref": -1009876543210,
            },
            {
                "chat_id": -1009876543210,
                "chat_name": "Test Modlog",
                "mode": "modlog",
            },
        ],
        "puzzles": [
            {
                "id": "test_001",
                "type": "arithmetic",
                "question": "What is 2 + 2?",
                "choices": [
                    {"text": "3", "is_correct": False},
                    {"text": "4", "is_correct": True},
                    {"text": "5", "is_correct": False},
                ],
            },
            {
                "id": "test_002",
                "type": "common_sense",
                "question": "What color is the sky?",
                "choices": [
                    {"text": "Red", "is_correct": False},
                    {"text": "Blue", "is_correct": True},
                    {"text": "Green", "is_correct": False},
                ],
            },
        ],
    }


@pytest.fixture
def mock_database_engine() -> MagicMock:
    """Mock database engine for testing."""
    from unittest.mock import MagicMock
    engine = MagicMock()
    engine.connect = MagicMock()
    return engine
