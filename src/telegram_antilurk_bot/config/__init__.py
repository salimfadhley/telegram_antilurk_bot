"""Config module initialization."""

from .defaults import get_default_puzzles
from .loader import ConfigLoader, ConfigurationError
from .schemas import (
    ChannelEntry,
    ChannelOverride,
    ChannelsConfig,
    GlobalConfig,
    ProvenanceInfo,
    Puzzle,
    PuzzleChoice,
    PuzzlesConfig,
)

__all__ = [
    'GlobalConfig',
    'ChannelsConfig',
    'PuzzlesConfig',
    'ChannelEntry',
    'ChannelOverride',
    'Puzzle',
    'PuzzleChoice',
    'ProvenanceInfo',
    'ConfigLoader',
    'ConfigurationError',
    'get_default_puzzles',
]
